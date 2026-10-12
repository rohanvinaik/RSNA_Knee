"""THE FIELD'S STRUCTURAL READING: air, the leg closed, the axis, the profile, two basins, the seam.

Task 7.1 of `every-stage-renders`. Until 2026-10-12 this was three probes in `workbench/render/`
(`seam.py`, `structure.py`, `objects.py`) that each measured inside a drawing and ran by hand. The
founder: *"I don't run ANY by hand. ALL probes are supposed to be part of production."* The stage
contract puts a measurement in a stage and leaves a renderer to arrange it; so the probes'
measurements live here, retained in the record, and `knee.pictures.collapse` arranges them.

The founder's design, 2026-10-10, as the chapter records it and the probes carried it:

1. **Close the leg.** Air is what connects to the frame's border, after a level loose enough to
   admit air and tight enough to exclude the leg's interior -- "connectivity does the real work, so
   the exact level stops mattering". The leg is the rest with its holes filled. Both answer only
   *inside or outside the body*, never tissue against background; the MASK is filled, never the
   values, or a fracture disappears from the representation.
2. **Read the superior--inferior axis from the header,** never from the pixels: in-plane for
   sagittal and coronal, along the stack normal for axial. The frames are visibly rotated, so image
   rows are not the anatomical axis.
3. **The profile along that axis,** of the squint inside the leg's central third, superior first:
   the two objects appear as two plateaus and the seam between them as the dip.
4. **Two basins from two seeds placed by the axis alone** -- N = 2 is given by the anatomy -- and
   the seam is the divide between them: a relation between two objects, never a dark band hunted
   by intensity. Two weightings, one algorithm, a told sign: on a fluid-sensitive series the seam is
   bright, so the field is negated; the sign comes from the series table, never from the pixels.
5. **The darkest places inside the leg and the largest bright bodies,** on each weighting, because
   cortical bone is signal-void on both while the marrow's sign flips between them.

Every bar the probes carried is an ARGUMENT here, declared once in `StructureBars` with its
provenance; none is a literal in a body. Nothing here names anatomy: a basin is an index, a body
is a rank, and the words "superior" and "inferior" are the patient frame's, not a bone's. This
reading is a MEMBER beside the objects stage's interiors (B1): they measure the same field by
different lenses, both are kept, and where they disagree is information (the three-legged stool).

What is NOT here: the fuller mechanism the founder taught -- plateaus and the deepest dip read in
noise units, seeding the watershed with the plateau interiors -- which refines item 4's fifths and
is a later increment. The cross-weighting comparison of the two seams (the chapter's "two columns")
is the next consumer of this record and is declared, not built.
"""

from __future__ import annotations

import math
from collections.abc import Mapping
from dataclasses import dataclass, replace
from types import MappingProxyType
from typing import NamedTuple

import numpy as np
from scipy import ndimage
from skimage.segmentation import watershed

# CODES is named only by the PEP 316 `post:` lines in this module's docstrings, which
# CrossHair evaluates in this module's namespace; ruff cannot see a docstring's use of it.
from knee.absence import CODES, absence_code  # noqa: F401
from knee.collapse.physical import Squint, numeric_plane, physical_squint
from knee.compute.contracts import ComputeContract, contracted, handed_on

#: Which direction of the acquisition carries superior--inferior.
AXIS_CODES: tuple[str, ...] = ("rows", "columns", "normal", "ambiguous", "unreadable")

#: Along that direction, whether an increasing index goes superior (+z in LPS).
SUPERIOR_CODES: tuple[str, ...] = ("increasing", "decreasing", "unreadable")


def told_sign(flag: object) -> bool | None:
    """The told sign from the series table's fluid-sensitive flag: True for "1", False for "0".

    The sign comes from the table and never from the pixels (item 4 of the module docstring).
    Anything that is not one of the table's two words is not a sign, and `read_structure` then
    names the basins and the seam unread rather than guessing a weighting.

    post: __return__ in (True, False, None)
    """
    return {"1": True, "0": False}.get(flag) if isinstance(flag, str) else None


@dataclass(frozen=True, slots=True)
class StructureBars:
    """Every bar this reading uses, as arguments with their provenance. None is a literal in a body.

    border_quantile, level_factor, level_offset: the air level is `quantile(border values,
    border_quantile) * level_factor + level_offset`, the border being the plane's four edges. From
    the probes of 2026-10-10 (`seam.py`, `structure.py`, `objects.py`, one expression in all
    three); the probe's own words: "the level only has to be loose enough to include air and
    tight enough to exclude the leg's interior; connectivity does the real work".
    inside_coverage: a tile is inside the leg when MORE than this fraction of its places are;
    the probes' `> 0.5`.
    central_fraction: the profile reads the central fraction of the leg's extent across the axis;
    the founder's teaching as the chapter records it, "profile the leg's central third".
    seed_fraction: the first and last fraction of the inside extent along the axis seed the two
    basins; the probes' fifths. The fuller rule (plateau interiors) is a later increment.
    smoothing_sigma: the Gaussian sigma, in tiles, applied to the field before the watershed;
    the probe's 1.0.
    dark_quantile: the darkest places inside the leg are those at or below this quantile of the
    inside squint; the probe's fifth.
    bodies: how many of the largest bright bodies are ranked; the probe's three.
    histogram_bins: bins of the air's own histogram; the probe's 120.
    """

    border_quantile: float = 0.9
    level_factor: float = 2.0
    level_offset: float = 1.0
    inside_coverage: float = 0.5
    central_fraction: float = 1.0 / 3.0
    seed_fraction: float = 0.2
    smoothing_sigma: float = 1.0
    dark_quantile: float = 0.2
    bodies: int = 3
    histogram_bins: int = 120


@dataclass(frozen=True, slots=True)
class StructureReading:
    """One plane's structural reading, every value retained, every silence named.

    code: from `CODES`; why: one sentence. axis: `AXIS_CODES`; superior: `SUPERIOR_CODES`.
    air_level: the level the air was read at, NaN when not read. air, leg: (R, C) bool at native
    scale; a place that is not finite is in neither. histogram_counts (bins,) int64 and
    histogram_edges (bins+1,) float64: the air's own values; both empty when there is no air.
    squint: `Squint` over the plane with every place outside the leg set to NaN, so its coverage
    says how much of each tile is leg; None when not read. inside: (tiles) bool, coverage above
    `inside_coverage`. profile: (steps,) float64 along the axis, SUPERIOR FIRST, NaN where the
    central band holds no inside tile; profile_tiles (steps,) int64, the tile index each step came
    from, in the same order; dip: the index into `profile` of its minimum, -1 when none is finite.
    basins: (tiles) int8, 0 outside, 1 and 2 the two basins; seam: (tiles) bool, a tile of one
    basin with a four-neighbour in the other. dark_level: NaN when not read; dark: (tiles) bool,
    inside at or below it; bodies: (tiles) int32, 0 or the rank 1..`bars.bodies` of the largest
    bright bodies. counts: air_places, leg_places, unread_places, inside_tiles, bodies_total.
    The profile, the basins and the seam are empty, and `why` says why, when the axis is not
    in-plane or the fluid-sensitive flag was not given: nothing is substituted.
    """

    code: str
    why: str
    axis: str
    superior: str
    air_level: float
    air: np.ndarray
    leg: np.ndarray
    histogram_counts: np.ndarray
    histogram_edges: np.ndarray
    squint: Squint | None
    inside: np.ndarray
    profile: np.ndarray
    profile_tiles: np.ndarray
    dip: int
    basins: np.ndarray
    seam: np.ndarray
    dark_level: float
    dark: np.ndarray
    bodies: np.ndarray
    counts: Mapping[str, int]


def axis_code(along_rows_z: float, along_columns_z: float, normal_z: float) -> str:
    """Which direction carries superior--inferior: the one whose LPS z cosine is largest in size.

    `along_rows_z` is the z component of the direction along which the ROW index increases
    (DICOM's second triplet), `along_columns_z` of the column-increasing direction (the first
    triplet), `normal_z` of the slice normal. Total: a non-finite cosine anywhere is `unreadable`,
    and an exact tie for the largest is `ambiguous`, never broken by argument order.

    post: __return__ in AXIS_CODES
    """
    sizes = (abs(along_rows_z), abs(along_columns_z), abs(normal_z))
    if not all(math.isfinite(size) for size in sizes):
        return "unreadable"
    top = max(sizes)
    if sizes.count(top) > 1:
        return "ambiguous"
    return ("rows", "columns", "normal")[sizes.index(top)]


def superior_code(z: float) -> str:
    """Along the chosen direction, whether an increasing index goes superior, which is +z in LPS.

    Zero carries no direction and is `unreadable`, as is anything non-finite.

    post: __return__ in SUPERIOR_CODES
    """
    if not math.isfinite(z) or z == 0.0:
        return "unreadable"
    return "increasing" if z > 0.0 else "decreasing"


def structure_code(plane_returned: bool, plane_readable: bool, leg_places: int) -> str:
    """The reading's own code: the shared vocabulary over what the plane gave.

    No plane is `predecessor_absent`; a plane that does not read as one 2-D numeric field is
    `invalid_count`; a readable plane in which no place is leg is `predecessor_empty` (the reading
    was made and the whole field is air or unread); otherwise `present`.

    post: __return__ in CODES
    post: __return__ != "present" or (plane_returned and plane_readable and leg_places > 0)
    """
    return absence_code(
        construction_built=True,
        predecessor_returned=plane_returned,
        item_count=leg_places if plane_readable else -1,
        item_read=True,
    )


CONTRACT = ComputeContract(
    kind="field_structural_reading",
    language="NumPy with SciPy ndimage (label, fill, gaussian) and scikit-image watershed; no twin",
    reads=(
        "plane: one 2-D numeric native plane (R,C), unwritten; orientation (6,) and normal (3,) "
        "LPS cosines as stored; spacing_rc mm; tile_mm; the fluid-sensitive flag; StructureBars"
    ),
    writes=(
        "owned read-only masks: air and leg bool (R,C); tile maps inside, basins, seam, dark, "
        "bodies over the squint's tile grid; the air histogram; the profile and its tiles; "
        "named codes and counts; no identity of anything"
    ),
    allocation=(
        "O(R*C) for the two native masks and the label scratch; O(tiles) for every tile map; "
        "no copy of the volume"
    ),
    work=(
        "one connected-component pass and one hole fill over R*C places; one squint (per-tile "
        "medians); one Gaussian and one watershed over the tiles; one component pass over the "
        "bright tiles; one histogram over the air places"
    ),
    parallel_unit="independent plane (not concurrently enabled)",
    reference="read_structure",
    proof_gate=(
        "intent tests on synthetic two-body planes under both weightings, both signs; "
        "real-entry receipt and the field frame"
    ),
)


@contracted
def read_structure(
    plane: object,
    orientation: object,
    normal: object,
    spacing_rc: tuple[float, float],
    tile_mm: float,
    fluid_sensitive: bool | None,
    bars: StructureBars,
) -> StructureReading:
    """Read the field's structure from one plane, or name the silence met. Total; never raises.

    See the module docstring for the five readings and `StructureReading` for every field. The
    order of work: the air and the leg at native scale; the air histogram; the squint inside the
    leg and the inside tiles; the axis from the header; the profile superior first and its dip;
    the two basins and the seam under the told sign; the darkest places and the largest bodies.

    A missing plane, an unreadable plane, a missing header, an axis that is not in-plane and a
    fluid-sensitive flag that is not a bool each return what could be read and name, in `why`,
    what could not; no value is substituted for a reading not made.

    post: __return__.code in CODES
    post: __return__.axis in AXIS_CODES
    post: __return__.superior in SUPERIOR_CODES
    post: __return__.air.shape == __return__.leg.shape
    """
    returned = plane is not None
    array = _numeric_plane(plane)
    # The axis is a header fact and is read whatever the plane holds: a missing, malformed or
    # all-air plane still has a header, and "unreadable" would otherwise name a header nobody
    # read (the route's first run surfaced exactly that on an axial plane with no leg).
    axis, superior = _header_codes(orientation, normal)
    if array is None:
        return _silent(
            structure_code(returned, False, 0),
            _BAD_PLANE if returned else _NO_PLANE,
            axis,
            superior,
        )
    problem = _scale_problem(spacing_rc, tile_mm) or _bar_problem(bars)
    if problem:
        return _silent(structure_code(returned, False, 0), problem, axis, superior)
    return _read_array(
        array, axis, superior, spacing_rc, tile_mm, fluid_sensitive, bars
    )


# ---------------------------------------------------------------------------------------------
# Private helpers. Each measures one thing and decides nothing: every code comes from the
# decisions declared above, every bar is read from `StructureBars`, and every owned array is
# frozen with `handed_on` where the reading is assembled (after the last internal use of it).
# ---------------------------------------------------------------------------------------------

#: The counts every reading carries, so a consumer never guards for a missing key.
_COUNTS: tuple[str, ...] = (
    "air_places",
    "leg_places",
    "unread_places",
    "inside_tiles",
    "bodies_total",
)

#: The axes along which the profile, the basins and the seam can be read within the plane.
_IN_PLANE: tuple[str, ...] = ("rows", "columns")

_NO_PLANE = "no plane was returned for this study"
_BAD_PLANE = "the plane is not one 2-D numeric ndarray"
_NO_LEG = "no place is leg: the whole field is air or unread"
_NO_INSIDE = "no tile is inside the leg, so the profile and basins hold nothing"
_FLUID_UNREAD = "the fluid-sensitive flag was not given as a bool, so the basins and seam are not read"
_SEEDS_UNREAD = (
    "the inside extent along the axis is too short to seed two basins, "
    "so the basins and seam are not read"
)
_ALL_READ = (
    "air, leg, squint, profile, two basins, seam, darkest places and bodies were read"
)
_AXIS_UNREAD: Mapping[str, str] = MappingProxyType(
    {
        "unreadable": (
            "the header does not read as (6,) and (3,) finite arrays, so the axis is "
            "unreadable and the profile, basins and seam are not read"
        ),
        "ambiguous": (
            "the three z cosines tie for the largest, so the axis is ambiguous and the "
            "profile, basins and seam are not read"
        ),
        "normal": (
            "the superior-inferior axis runs along the stack normal, not in the plane, "
            "so the profile, basins and seam are not read"
        ),
    }
)

#: (bar, lowest, highest, lowest excluded): what each float bar must satisfy to be readable at
#: all. These bound what would raise or mean nothing; they do not choose a value for any bar.
_BAR_BOUNDS: tuple[tuple[str, float, float, bool], ...] = (
    ("border_quantile", 0.0, 1.0, False),
    ("level_factor", -math.inf, math.inf, False),
    ("level_offset", -math.inf, math.inf, False),
    ("inside_coverage", 0.0, 1.0, False),
    ("central_fraction", 0.0, 1.0, True),
    ("seed_fraction", 0.0, 0.5, True),
    ("smoothing_sigma", 0.0, math.inf, False),
    ("dark_quantile", 0.0, 1.0, False),
)

#: (bar, least): the integer bars and the least value each can take.
_COUNT_BARS: tuple[tuple[str, int], ...] = (("bodies", 0), ("histogram_bins", 1))


class _Tiles(NamedTuple):
    """What the squint inside the leg gave: the tile maps that need neither header nor sign."""

    squint: Squint
    inside: np.ndarray
    field: np.ndarray
    dark_level: float
    dark: np.ndarray
    bodies: np.ndarray
    bodies_total: int
    unread: str


class _Along(NamedTuple):
    """What the header gave: the axis, the way up, and the profile along it."""

    axis: str
    superior: str
    profile: np.ndarray
    profile_tiles: np.ndarray
    dip: int
    unread: str


class _Basins(NamedTuple):
    """The two basins and the seam between them, or zeros of the tile grid's shape."""

    basins: np.ndarray
    seam: np.ndarray
    unread: str


def _silent(
    code: str, why: str, axis: str = "unreadable", superior: str = "unreadable"
) -> StructureReading:
    """A reading in which nothing of the plane was read: every array empty in its declared dtype
    and counts zero. The axis and the way up are the header's, which is read even then."""
    flat = (0, 0)
    return StructureReading(
        code=code,
        why=why,
        axis=axis,
        superior=superior,
        air_level=math.nan,
        air=handed_on(np.zeros(flat, dtype=np.bool_)),
        leg=handed_on(np.zeros(flat, dtype=np.bool_)),
        histogram_counts=handed_on(np.zeros(0, dtype=np.int64)),
        histogram_edges=handed_on(np.zeros(0, dtype=np.float64)),
        squint=None,
        inside=handed_on(np.zeros(flat, dtype=np.bool_)),
        profile=handed_on(np.zeros(0, dtype=np.float64)),
        profile_tiles=handed_on(np.zeros(0, dtype=np.int64)),
        dip=-1,
        basins=handed_on(np.zeros(flat, dtype=np.int8)),
        seam=handed_on(np.zeros(flat, dtype=np.bool_)),
        dark_level=math.nan,
        dark=handed_on(np.zeros(flat, dtype=np.bool_)),
        bodies=handed_on(np.zeros(flat, dtype=np.int32)),
        counts=MappingProxyType(dict.fromkeys(_COUNTS, 0)),
    )


def _numeric_plane(plane: object) -> np.ndarray | None:
    """The plane itself when it is one 2-D numeric ndarray, else None. Nothing is converted."""
    if not isinstance(plane, np.ndarray):
        return None
    try:
        numeric_plane(plane)
    except ValueError:
        return None
    return plane


def _scale_problem(spacing_rc: tuple[float, float], tile_mm: float) -> str:
    """Why the squint cannot tile at this scale, or "". Asks `physical_squint` itself, on one place."""
    try:
        physical_squint(np.zeros((1, 1)), spacing_rc, tile_mm)
    except (TypeError, ValueError, OverflowError):
        return "spacing_rc or tile_mm cannot tile a plane"
    return ""


def _number(value: object) -> float | None:
    """The value as a finite float when it is a real number and not a bool, else None."""
    if isinstance(value, bool) or not isinstance(
        value, (int, float, np.integer, np.floating)
    ):
        return None
    try:
        number = float(value)
    except OverflowError:
        return None
    return number if math.isfinite(number) else None


def _bar_problem(bars: object) -> str:
    """Why the bars cannot be read, or "". It checks what would raise or mean nothing, no more."""
    if not isinstance(bars, StructureBars):
        return "bars is not a StructureBars"
    for name, lowest, highest, lowest_excluded in _BAR_BOUNDS:
        value = _number(getattr(bars, name))
        if (
            value is None
            or not lowest <= value <= highest
            or (lowest_excluded and value == lowest)
        ):
            return f"bar {name} cannot be read"
    for name, least in _COUNT_BARS:
        value = getattr(bars, name)
        if (
            isinstance(value, bool)
            or not isinstance(value, (int, np.integer))
            or value < least
        ):
            return f"bar {name} cannot be read"
    return ""


def _read_array(
    plane: np.ndarray,
    axis: str,
    superior: str,
    spacing_rc: tuple[float, float],
    tile_mm: float,
    fluid_sensitive: bool | None,
    bars: StructureBars,
) -> StructureReading:
    """The reading of a plane whose arguments all read, in the order the docstring gives."""
    finite = np.isfinite(plane)
    level, air, leg = _air_and_leg(plane, finite, bars)
    leg_places = int(np.count_nonzero(leg))
    histogram_counts, histogram_edges = _air_histogram(plane, air, bars.histogram_bins)
    native = {
        "air_places": int(np.count_nonzero(air)),
        "leg_places": leg_places,
        "unread_places": int(finite.size - np.count_nonzero(finite)),
    }
    reading = replace(
        _silent(structure_code(True, True, leg_places), _NO_LEG, axis, superior),
        air_level=level,
        air=handed_on(air),
        leg=handed_on(leg),
        histogram_counts=handed_on(histogram_counts),
        histogram_edges=handed_on(histogram_edges),
        counts=MappingProxyType({**native, "inside_tiles": 0, "bodies_total": 0}),
    )
    if leg_places == 0:
        return reading
    tiles = _tile_stage(plane, leg, spacing_rc, tile_mm, bars)
    along = _axis_stage(tiles.field, axis, superior, bars)
    two = _basin_stage(tiles, along, fluid_sensitive, bars)
    unread = [clause for clause in (tiles.unread, along.unread, two.unread) if clause]
    counts = {
        **native,
        "inside_tiles": int(np.count_nonzero(tiles.inside)),
        "bodies_total": tiles.bodies_total,
    }
    return replace(
        reading,
        why="; ".join(unread) if unread else _ALL_READ,
        axis=along.axis,
        superior=along.superior,
        squint=tiles.squint,
        inside=handed_on(tiles.inside),
        profile=handed_on(along.profile),
        profile_tiles=handed_on(along.profile_tiles),
        dip=along.dip,
        basins=handed_on(two.basins),
        seam=handed_on(two.seam),
        dark_level=tiles.dark_level,
        dark=handed_on(tiles.dark),
        bodies=handed_on(tiles.bodies),
        counts=MappingProxyType(counts),
    )


def _border(grid: np.ndarray) -> np.ndarray:
    """The values on the four edges of a 2-D grid, corners twice; empty for an empty grid."""
    if grid.size == 0:
        return grid.reshape(-1)[:0]
    return np.concatenate([grid[0], grid[-1], grid[:, 0], grid[:, -1]])


def _air_and_leg(
    plane: np.ndarray, finite: np.ndarray, bars: StructureBars
) -> tuple[float, np.ndarray, np.ndarray]:
    """(air level, air, leg) at native scale; the air level is NaN when it could not be read.

    The level is the border rule of the probes: `quantile(border, border_quantile) * level_factor
    + level_offset` over the finite places on the plane's four edges. Air is the low, finite
    places that connect (four-connected) to the border; the leg is the rest with its holes
    filled, restricted to finite places. A place that is not finite is in neither. A plane with
    no finite place on its border has no level, so no place is claimed as air or as leg.

    Every air component touches the border by construction, so the complement of `~air` holds no
    enclosed component and the hole fill leaves `~air` as it was: what closes the leg is the
    air's definition by connection to the border. The fill is kept because the declared work
    names it and it costs one pass; `binary_fill_holes` fills the MASK and never the values.
    """
    border = _border(plane)
    border = border[np.isfinite(border)]
    if border.size == 0:
        nothing = np.zeros(plane.shape, dtype=np.bool_)
        return math.nan, nothing, nothing.copy()
    level = (
        float(np.quantile(border, bars.border_quantile)) * bars.level_factor
        + bars.level_offset
    )
    labels, count = ndimage.label(finite & (plane <= level))
    touching = np.zeros(count + 1, dtype=np.bool_)
    touching[_border(labels)] = True
    touching[0] = False
    air = touching[labels]
    leg = ndimage.binary_fill_holes(~air) & finite
    return level, air, leg


def _air_histogram(
    plane: np.ndarray, air: np.ndarray, bins: int
) -> tuple[np.ndarray, np.ndarray]:
    """The air's own values as (counts int64 (bins,), edges float64 (bins+1,)); both empty with no air."""
    if not air.any():
        return np.zeros(0, dtype=np.int64), np.zeros(0, dtype=np.float64)
    counts, edges = np.histogram(plane[air].astype(np.float64), bins=bins)
    return counts.astype(np.int64, copy=False), edges


def _squint_in_leg(
    plane: np.ndarray, leg: np.ndarray, spacing_rc: tuple[float, float], tile_mm: float
) -> Squint:
    """The squint of the plane with every place outside the leg NaN, so `coverage` is the leg share.

    The values inside the leg are copied as they are: only the mask closes the leg, and a hole's
    own values still reach the squint of its tile.
    """
    inside_leg = np.full(plane.shape, np.nan, dtype=np.float64)
    np.copyto(inside_leg, plane, where=leg)
    return physical_squint(inside_leg, spacing_rc, tile_mm)


def _tile_stage(
    plane: np.ndarray,
    leg: np.ndarray,
    spacing_rc: tuple[float, float],
    tile_mm: float,
    bars: StructureBars,
) -> _Tiles:
    """The squint inside the leg, the inside tiles, and the darkest places and largest bodies.

    `field` is the squint median at the inside tiles and NaN elsewhere, as the probes' `sq` was:
    a partly covered edge tile has a finite median and is not inside, and must not reach the
    smoothing or the profile. The darkest places and the bodies read the median as it is, on
    either weighting, so they need neither the header nor the told sign.
    """
    squint = _squint_in_leg(plane, leg, spacing_rc, tile_mm)
    inside = squint.coverage > bars.inside_coverage
    field = np.where(inside, squint.median, np.nan)
    dark_level, dark, bodies, total = _dark_and_bodies(field, inside, bars)
    unread = "" if inside.any() else _NO_INSIDE
    return _Tiles(squint, inside, field, dark_level, dark, bodies, total, unread)


def _dark_and_bodies(
    field: np.ndarray, inside: np.ndarray, bars: StructureBars
) -> tuple[float, np.ndarray, np.ndarray, int]:
    """(dark level, dark tiles, body ranks, bodies in all): the darkest places inside the leg and
    the `bars.bodies` largest four-connected components of the inside tiles above that level.

    Ranks are 1 for the largest; equal sizes keep the order scipy numbers the components in, so
    the ranking is deterministic. The total counts every component, not only the ranked ones.
    """
    if not inside.any():
        return (
            math.nan,
            np.zeros(inside.shape, dtype=np.bool_),
            np.zeros(inside.shape, dtype=np.int32),
            0,
        )
    level = float(np.quantile(field[inside], bars.dark_quantile))
    dark = inside & (field <= level)
    labels, total = ndimage.label(inside & (field > level))
    sizes = np.bincount(labels.ravel(), minlength=total + 1)[1:]
    biggest = np.argsort(-sizes, kind="stable")[: bars.bodies]
    rank = np.zeros(total + 1, dtype=np.int32)
    rank[biggest + 1] = np.arange(1, biggest.size + 1, dtype=np.int32)
    return level, dark, rank[labels], int(total)


def _header_codes(orientation: object, normal: object) -> tuple[str, str]:
    """(axis, superior) from the header alone; both "unreadable" unless it reads as (6,) and (3,).

    `orientation[:3]` is the direction along which the column index increases and `orientation[3:]`
    the one along which the row index increases, so the z cosines handed to `axis_code` are
    `orientation[5]` (rows), `orientation[2]` (columns) and `normal[2]`. The way up is the sign
    of the chosen direction's z; an ambiguous axis has no chosen direction.
    """
    try:
        directions = np.asarray(orientation, dtype=np.float64)
        stack = np.asarray(normal, dtype=np.float64)
    except (TypeError, ValueError, OverflowError):
        return "unreadable", "unreadable"
    if directions.shape != (6,) or stack.shape != (3,):
        return "unreadable", "unreadable"
    if not (np.isfinite(directions).all() and np.isfinite(stack).all()):
        return "unreadable", "unreadable"
    z = {
        "rows": float(directions[5]),
        "columns": float(directions[2]),
        "normal": float(stack[2]),
    }
    axis = axis_code(z["rows"], z["columns"], z["normal"])
    return axis, superior_code(z[axis]) if axis in z else "unreadable"


def _axis_stage(
    field: np.ndarray, axis: str, superior: str, bars: StructureBars
) -> _Along:
    """The profile along the header's axis, when that axis lies in the plane."""
    if axis not in _IN_PLANE:
        return _Along(
            axis,
            superior,
            np.zeros(0, dtype=np.float64),
            np.zeros(0, dtype=np.int64),
            -1,
            _AXIS_UNREAD[axis],
        )
    profile, tiles = _profile(field, axis, superior, bars.central_fraction)
    return _Along(axis, superior, profile, tiles, _dip(profile), "")


def _along_first(tile_map: np.ndarray, axis: str, superior: str) -> np.ndarray:
    """A tile map as (steps along the axis, across it), the superior step first. A view."""
    view = tile_map if axis == "rows" else tile_map.T
    return view[::-1] if superior == "increasing" else view


def _from_along_first(along: np.ndarray, axis: str, superior: str) -> np.ndarray:
    """The inverse of `_along_first`: back to the tile grid's own axes. A view."""
    view = along[::-1] if superior == "increasing" else along
    return view if axis == "rows" else view.T


def _profile(
    field: np.ndarray, axis: str, superior: str, central_fraction: float
) -> tuple[np.ndarray, np.ndarray]:
    """(profile, tile index of each step): per-step median of the inside squint, superior first.

    The inside extent across the axis is the span of indices that hold an inside tile; the
    profile reads its central `central_fraction`, which is what remains after trimming
    `floor(extent * (1 - central_fraction) / 2)` indices from each side. A step whose band holds
    no inside tile is NaN, never zero. Only steps with a finite value are reduced, so no
    all-NaN reduction is ever asked for.
    """
    along = _along_first(field, axis, superior)
    steps = along.shape[0]
    index = np.arange(steps, dtype=np.int64)
    tiles = index[::-1].copy() if superior == "increasing" else index
    profile = np.full(steps, np.nan, dtype=np.float64)
    across = np.flatnonzero(np.isfinite(along).any(axis=0))
    if across.size:
        first, last = int(across[0]), int(across[-1])
        trim = max(0, math.floor((last - first + 1) * (1.0 - central_fraction) / 2.0))
        band = along[:, first + trim : last + 1 - trim]
        read = np.isfinite(band).any(axis=1)
        profile[read] = np.nanmedian(band[read], axis=1)
    return profile, tiles


def _dip(profile: np.ndarray) -> int:
    """The index of the profile's minimum among its finite steps (the first on a tie); -1 when none."""
    finite = np.isfinite(profile)
    if not finite.any():
        return -1
    return int(np.argmin(np.where(finite, profile, np.inf)))


def _seeds(inside_along: np.ndarray, fraction: float) -> np.ndarray | None:
    """Seeds 1 and 2 in the superior-first frame, or None when either seed would be empty.

    Along the inside extent of `n` steps (first to last step holding an inside tile), seed 1 is
    the first `floor(n * fraction)` steps and seed 2 the last `ceil(n * fraction)`, which is the
    probes' `n // 5` and `n - 4 * n // 5` for a fifth. Only inside tiles are seeded. With one
    seed empty a watershed would label the whole mask as the other basin, so none is run.
    """
    steps = np.flatnonzero(inside_along.any(axis=1))
    if steps.size == 0:
        return None
    first, last = int(steps[0]), int(steps[-1])
    extent = last - first + 1
    head = math.floor(extent * fraction)
    tail = math.ceil(extent * fraction)
    if head < 1:
        return None
    seeds = np.zeros(inside_along.shape, dtype=np.int32)
    seeds[first : first + head] = 1
    seeds[last + 1 - tail : last + 1] = 2
    seeds[~inside_along] = 0
    return seeds


def _basins(
    field: np.ndarray,
    inside: np.ndarray,
    axis: str,
    superior: str,
    fluid_sensitive: bool,
    bars: StructureBars,
) -> np.ndarray | None:
    """The two basins (int8: 0 outside, 1 and 2) by watershed from two seeds placed by the axis.

    Basin 1 is seeded at the superior end of the inside extent and basin 2 at the inferior end,
    so the numbering means the same side in every acquisition whatever its row order. The field
    is the inside squint median, negated when the series is told to be fluid-sensitive (the
    seam is bright there), with the places outside the inside tiles filled by the field's
    minimum before the Gaussian. None when the extent is too short to seed both basins.
    """
    seeds_along = _seeds(_along_first(inside, axis, superior), bars.seed_fraction)
    if seeds_along is None:
        return None
    seeds = np.ascontiguousarray(_from_along_first(seeds_along, axis, superior))
    signed = -field if fluid_sensitive else field
    filled = np.where(inside, signed, signed[inside].min())
    smooth = ndimage.gaussian_filter(filled, bars.smoothing_sigma)
    return watershed(-smooth, markers=seeds, mask=inside).astype(np.int8)


def _faces(tiles: np.ndarray, others: np.ndarray) -> np.ndarray:
    """The tiles of `tiles` that have a four-neighbour in `others`."""
    near = np.zeros_like(others)
    near[1:, :] |= others[:-1, :]
    near[:-1, :] |= others[1:, :]
    near[:, 1:] |= others[:, :-1]
    near[:, :-1] |= others[:, 1:]
    return tiles & near


def _seam(basins: np.ndarray) -> np.ndarray:
    """The tiles of one basin with a four-neighbour in the other: a relation, never a dark band."""
    one, two = basins == 1, basins == 2
    return _faces(one, two) | _faces(two, one)


def _basin_stage(
    tiles: _Tiles, along: _Along, fluid_sensitive: bool | None, bars: StructureBars
) -> _Basins:
    """The basins and seam under the told sign, or zeros of the tile grid saying why not."""
    nothing = (
        np.zeros(tiles.inside.shape, dtype=np.int8),
        np.zeros(tiles.inside.shape, dtype=np.bool_),
    )
    if not isinstance(fluid_sensitive, bool):
        return _Basins(*nothing, _FLUID_UNREAD)
    if along.axis not in _IN_PLANE or not tiles.inside.any():
        return _Basins(*nothing, "")
    basins = _basins(
        tiles.field, tiles.inside, along.axis, along.superior, fluid_sensitive, bars
    )
    if basins is None:
        return _Basins(*nothing, _SEEDS_UNREAD)
    return _Basins(basins, _seam(basins), "")
