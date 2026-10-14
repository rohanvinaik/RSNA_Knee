"""Name the objects of one plane where lenses that each measure one thing concur; abstain elsewhere.

His words, 2026-10-13: «"never wrong" simply means you are not saying something false», and «This
relies on a series of lossy lenses, with the "truth" being recapitulated from addative and subtractive
superposition of the lossy lenses». So every LENS here measures one property of every place or of
every territory and knows no question. Every QUESTION (air, skin, bone, femur and tibia, joint) holds
its own signs, reads each sign as +1, 0 or -1 from one lens, names an object only where its signs
concur, and otherwise abstains with a named code. Every lens's readings are returned, so the run keeps
them.

The signs are medicine's, from docs/OBJECTS_AND_CONDITIONS.md, cited by its source keys; a line that is
Claude's own says so. One scale recurs, and it is not new: `reach_mm`, the half-width of the window the
interiors stage reads a border over (its offsets run from -3 to 3 mm), handed in by the caller. Nothing
here draws; the run's renderer draws what this returns.
"""

from dataclasses import dataclass

import numpy as np
from scipy import ndimage as ndi

from knee.objects.interiors import EDGE_KINDS, TRACE_CODES, InteriorReading

# The cosine of 45 degrees: more along an axis than across it. Geometry, not a fitted level.
HALF_TURN_SHARE = float(np.sqrt(0.5))
OBJECT_CODES = {
    "unassigned": 0,
    "air": 1,
    "skin": 2,
    "femur": 3,
    "tibia": 4,
    "joint": 5,
}
# The bone answers the femur and tibia question may seat: concurrence, or a wall whose signal the
# sequence leaves silent. That question then needs its own signs to concur before it names either.
PAIR_CANDIDATES = ("bone_concurred", "abstain_signal_silent")
UNREADABLE_EDGES = (EDGE_KINDS["frame"], EDGE_KINDS["acquisition_missing"])


@dataclass(frozen=True, slots=True)
class TerritoryReading:
    """One territory's lens readings, each a measurement, and its bone question's answer.

    The walled part is the territory's share of its deepest place's compartment; every reading
    after `walled_pixels` is taken over that part. `wall_share` is NaN when no border edge of it
    could be read.
    """

    territory: int
    pixels: int
    walled_pixels: int
    depth_mm: float
    peak_rc: tuple[int, int]
    superior_mm: float
    signal_third: int | None
    wall_share: float
    border_edges: int
    wall_sign: int
    marrow_sign: int
    fat_sign: int
    bone: str


@dataclass(frozen=True, slots=True)
class PlaneAssignment:
    """One plane's named objects (`OBJECT_CODES`), the field lenses that named them, and the codes."""

    objects: np.ndarray
    margin: np.ndarray
    record_edge: np.ndarray
    inside: np.ndarray
    walled: np.ndarray
    readings: tuple[TerritoryReading, ...]
    codes: dict[str, str]
    counts: dict[str, int]
    femur: int | None
    tibia: int | None
    superior_in_plane: float


def unrecorded(plane: np.ndarray) -> np.ndarray:
    """Stored zeros joined to the frame through zeros: a margin the reconstruction never filled.

    Measured on the proof study, 2026-10-14: every series stores whole sides of its frame as exact
    zero around a slightly turned rectangle of content. A zero there reads nothing, so nothing is
    named in it.
    """
    zeros = plane == 0
    if not zeros.any():
        return zeros
    parts, _ = ndi.label(zeros)
    frame = np.concatenate((parts[0], parts[-1], parts[:, 0], parts[:, -1]))
    return np.isin(parts, frame[frame > 0])


def record_edge(
    margin: np.ndarray, spacing_rc: tuple[float, float], reach_mm: float
) -> np.ndarray:
    """Recorded places within `reach_mm` of the margin or the frame, where the record ends and blends."""
    if not margin.size:
        return margin.copy()
    recorded = np.pad(~margin, 1, constant_values=False)
    distance = ndi.distance_transform_edt(recorded, sampling=spacing_rc)[1:-1, 1:-1]
    return ~margin & (distance <= reach_mm)


def closed(
    mask: np.ndarray, spacing_rc: tuple[float, float], radius_mm: float
) -> np.ndarray:
    """`mask` closed by a disc of `radius_mm`; the frame repeats its edge, so it adds nothing."""
    if not mask.size:
        return mask.copy()
    half = np.ceil(radius_mm / np.asarray(spacing_rc)).astype(int)
    rows, cols = np.mgrid[-half[0] : half[0] + 1, -half[1] : half[1] + 1]
    disc = (rows * spacing_rc[0]) ** 2 + (cols * spacing_rc[1]) ** 2 <= radius_mm**2
    pad = int(half.max()) + 1
    padded = np.pad(mask, pad, mode="edge")
    return ndi.binary_closing(padded, structure=disc)[pad:-pad, pad:-pad]


def compartments(
    dark: np.ndarray,
    available: np.ndarray,
    spacing_rc: tuple[float, float],
    reach_mm: float,
) -> np.ndarray:
    """The field's above-split places, cut apart where low signal closes across `reach_mm` (labels).

    A gap in a wall of low signal no wider than the border window (a cortex read above the split
    for a few places) is sealed, so what lies behind the gap is another compartment.
    """
    parts, _ = ndi.label(available & ~closed(dark, spacing_rc, reach_mm))
    return parts


def edge_places(
    points_rc: np.ndarray, normals_rc: np.ndarray, shape: tuple[int, ...]
) -> tuple[np.ndarray, np.ndarray]:
    """Each border edge's two places: the territory's own, and its neighbour's (clipped to the plane)."""
    step = np.sign(normals_rc)
    limit = np.asarray(shape) - 1
    inner = np.clip(np.rint(points_rc - step / 2).astype(int), 0, limit)
    outer = np.clip(np.rint(points_rc + step / 2).astype(int), 0, limit)
    return inner, outer


def signal_third(value: float, thirds: tuple[float, float]) -> int | None:
    """-1, 0 or +1: which third of the series' above-split values `value` falls in; None unread."""
    low, high = thirds
    if not (np.isfinite(low) and np.isfinite(high) and np.isfinite(value)):
        return None
    return -1 if value < low else (1 if value > high else 0)


def marrow_sign(third: int | None, fluid_sensitive: str, fat_suppressed: str) -> int:
    """+1, 0 or -1: what a signal third says of bone marrow on this kind of sequence.

    From the tissue table (docs/OBJECTS_AND_CONDITIONS.md §3, [Kh] Table II). T1W, tags (0, 0):
    yellow marrow is high, so the bright third carries its signal (+1); red marrow is low or
    intermediate, so the lower thirds refuse nothing (0). Fat-suppressed, tags (1, 1): yellow
    marrow is very low, so the dark third carries the suppressed signal (+1); red marrow, muscle,
    fat and cartilage all reach the middle third (0); no marrow is bright while fluid is very high,
    so the bright third refuses it (-1). T2W or PD without suppression (1, 0), and any other
    pairing: the table gives marrow no signal of its own (0).
    """
    if third is None:
        return 0
    if (fluid_sensitive, fat_suppressed) == ("0", "0"):
        return 1 if third > 0 else 0
    if (fluid_sensitive, fat_suppressed) == ("1", "1"):
        return -1 if third > 0 else (1 if third < 0 else 0)
    return 0


def fat_sign(third: int | None, fluid_sensitive: str, fat_suppressed: str) -> int:
    """+1, 0 or -1: what a signal third says of fat on this kind of sequence.

    From the same table. T1W (0, 0): fat is high, so the bright third carries its signal (+1) and
    the dark third refuses it (-1). Fat-suppressed (1, 1): fat is low to intermediate and never
    bright, so the bright third refuses it (-1) and the others say nothing (0). Any other
    pairing: nothing (0).
    """
    if third is None:
        return 0
    if (fluid_sensitive, fat_suppressed) == ("0", "0"):
        return 1 if third > 0 else (-1 if third < 0 else 0)
    if (fluid_sensitive, fat_suppressed) == ("1", "1"):
        return -1 if third > 0 else 0
    return 0


def wall_sign(bracketed: int, readable: int) -> int:
    """+1, 0 or -1: whether a thin dark band walls most of a territory's readable border.

    A bone is walled by its cortex, very low on every sequence ([Kh]); the interiors stage reads a
    thin dark band with tissue beyond it as a bracketed trace. "Most" is a majority, at least half:
    Claude's bar, from common sense, never fitted. 0 when no border edge could be read.
    """
    if readable <= 0:
        return 0
    return 1 if 2 * bracketed >= readable else -1


def bone_code(wall: int, marrow: int) -> str:
    """Bone where its two signs concur: the cortex's wall and the marrow's signal.

    [Kh]: bone is told from the soft tissue around it «by the very-low cortex and the marrow's fat
    signal». A sign the sequence leaves silent (0) neither agrees nor refuses, and one voice is not
    concurrence, so the question stays open; measured 2026-10-14, the wall alone was met by air
    and muscle territories on a coronal T1W. A sign against the other also leaves it open.
    """
    if wall == 0:
        return "abstain_wall_unread"
    if wall > 0:
        if marrow > 0:
            return "bone_concurred"
        return "abstain_signal_silent" if marrow == 0 else "abstain_signs_disagree"
    return "abstain_signs_disagree" if marrow > 0 else "not_bone"


def place_signs(
    plane: np.ndarray, thirds: tuple[float, float], tags: tuple[str, str], sign
) -> np.ndarray:
    """`sign` (`marrow_sign` or `fat_sign`) read place by place from each place's own third.

    0 wherever the thirds are unread or a value is not finite: a sign not read says nothing.
    """
    low, high = thirds
    value = np.asarray(plane, dtype=np.float64)
    signs = np.zeros(plane.shape, dtype=np.int8)
    if not (np.isfinite(low) and np.isfinite(high)):
        return signs
    third = np.where(value < low, -1, np.where(value > high, 1, 0))
    for t in (-1, 0, 1):
        signs[(third == t) & np.isfinite(value)] = sign(t, *tags)
    return signs


def taken_in(part: np.ndarray, refused: np.ndarray) -> np.ndarray:
    """The refused places of `part` that run on, still refused, out of it: what it took in.

    Fluid that a bone's territory reached runs on out of the bone into the joint or a recess; a
    refused place the bone holds alone is its own reading (noise, or later a bruise's oedema), and
    stays the bone's. Measured 2026-10-14 on a coronal fat-suppressed tibia: refusing every bright
    place left the marrow speckled with holes.
    """
    parts, _ = ndi.label(refused)
    crossing = np.unique(parts[refused & ~part])
    return part & np.isin(parts, crossing[crossing > 0])


def held_body(mask: np.ndarray, peak_rc: tuple[int, int]) -> np.ndarray:
    """The connected piece of `mask` that holds `peak_rc`: one bone is one connected solid.

    A piece cut off from it (by fluid taken out, say) is not that bone. Empty when the peak itself
    is not in `mask`.
    """
    parts, _ = ndi.label(mask)
    own = parts[peak_rc]
    return parts == own if own else np.zeros(mask.shape, dtype=bool)


def pair_code(
    superior_in_plane: float, bones: int, open_deeper: int, stacked: bool, crossed: bool
) -> str:
    """Femur over tibia: the two deepest candidates, stacked along the leg's axis, low signal between.

    The femur and tibia are the knee's two large bones and meet at the tibiofemoral joint
    ([R-KNEE]); the leg lies along the patient's superior axis. A candidate is a territory whose
    bone question concurred or stood open only on a silent signal (`PAIR_CANDIDATES`). Abstains
    when that axis does not lie in the plane, when there are fewer than two candidates, when a
    territory at least as deep as the second left its bone question open for another reason (it
    could be the bone that was missed), when the two are not stacked, or when no low signal lies
    between them.
    """
    if not np.isfinite(superior_in_plane) or superior_in_plane < HALF_TURN_SHARE:
        return "abstain_superior_through_plane"
    if bones < 2:
        return "abstain_fewer_than_two_bones"
    if open_deeper:
        return "abstain_deeper_territory_open"
    if not stacked:
        return "abstain_two_deepest_bones_not_stacked"
    if not crossed:
        return "abstain_no_low_signal_between"
    return "femur_tibia"


def joint_code(fat: int) -> str:
    """What an above-split place between the femur and the tibia is named, by its own fat sign.

    The joint holds cartilage and fluid ([C], [Kh]); the fat pads are objects of their own that
    border it, and Hoffa's «follows the signal of subcutaneous fat on all pulse sequences» ([Kh]).
    So a place there is joint where its signal refuses fat (-1: fluid's, low on T1W and very high
    under fat suppression), and abstains where it carries fat's (+1, a fat pad or marrow) or says
    nothing (0, where cartilage and fat cannot be told apart by signal).
    """
    if fat < 0:
        return "joint"
    return "abstain_fat_signal" if fat > 0 else "abstain_signal_silent"


def air_code(
    body: int, outside: int, outside_dark: int, open_dark: int, air: int
) -> str:
    """Whether air was named, or why not, from the counts of the places each sign kept."""
    if air:
        return "identified"
    if not body:
        return "abstain_no_body"
    if not outside:
        return "abstain_no_outside_field"
    if not outside_dark:
        return "abstain_outside_not_low_signal"
    if not open_dark:
        return "abstain_low_signal_only_at_record_edge"
    return "abstain_no_low_signal_wider_than_a_border"


def low_signal_between(dark: np.ndarray, a_rc, b_rc) -> bool:
    """Whether the straight path between two places crosses measured low signal."""
    a, b = np.asarray(a_rc, dtype=np.float64), np.asarray(b_rc, dtype=np.float64)
    steps = int(np.ceil(2 * np.abs(b - a).max())) + 1
    path = np.rint(a + np.linspace(0, 1, steps)[:, None] * (b - a)).astype(int)
    return bool(dark[path[:, 0], path[:, 1]].any())


def superior_share(basis_lps: np.ndarray, a_rc, b_rc) -> float:
    """How much of the patient vector from a to b lies along the superior axis (0 to 1)."""
    v = basis_lps @ (
        np.asarray(b_rc, dtype=np.float64) - np.asarray(a_rc, dtype=np.float64)
    )
    norm = float(np.linalg.norm(v))
    return abs(float(v[2])) / norm if norm else float("nan")


def between_along_superior(
    upper: np.ndarray, lower: np.ndarray, basis_lps: np.ndarray
) -> np.ndarray:
    """The places strictly between `upper` and `lower` on lines along the in-plane superior axis.

    The line is the pixel axis nearer the superior axis; along it, from the last `upper` place to
    the first `lower` place, wherever both lie on the line in that order.
    """
    rows_axis = abs(basis_lps[2, 0]) >= abs(basis_lps[2, 1])
    a, b = (upper, lower) if rows_axis else (upper.T, lower.T)
    superior_step = basis_lps[2, 0] if rows_axis else basis_lps[2, 1]
    if superior_step > 0:  # superior lies toward larger indices: walk the other way
        a, b = a[::-1], b[::-1]
    index = np.arange(a.shape[0])[:, None]
    last_upper = np.where(a, index, -1).max(axis=0, initial=-1)
    first_lower = np.where(b, index, a.shape[0]).min(axis=0, initial=a.shape[0])
    present = (
        (last_upper >= 0) & (first_lower < a.shape[0]) & (last_upper < first_lower)
    )
    between = present & (index > last_upper) & (index < first_lower)
    if superior_step > 0:
        between = between[::-1]
    return between if rows_axis else between.T


def territory_readings(
    plane: np.ndarray,
    reading: InteriorReading,
    readable: np.ndarray,
    compartment: np.ndarray,
    basis_lps: np.ndarray,
    thirds: tuple[float, float],
    tags: tuple[str, str],
) -> tuple[tuple[TerritoryReading, ...], np.ndarray]:
    """Every territory's lens readings over its walled part, and the map of the walled parts."""
    labels, distance = reading.labels, reading.distance_mm
    count = int(labels.max(initial=0))
    walled = np.zeros(labels.shape, dtype=np.int32)
    found = []
    for territory in range(1, count + 1):
        mask = labels == territory
        if not mask.any():
            continue
        depth = float(distance[mask].max())
        peak = np.argwhere(mask & (distance == depth))[0]
        own = compartment[peak[0], peak[1]]
        if own:
            walled[mask & (compartment == own)] = territory
        found.append((territory, mask, depth, peak))
    inner, _ = edge_places(
        reading.edge_points_rc, reading.edge_normals_rc, labels.shape
    )
    regions = reading.edge_regions.astype(np.int64)
    mine = readable & (walled[inner[:, 0], inner[:, 1]] == regions)
    bracketed = (reading.edge_kinds == EDGE_KINDS["low_signal"]) & (
        reading.trace_codes == TRACE_CODES["bracketed"]
    )
    readable_count = np.bincount(regions[mine], minlength=count + 1)
    bracketed_count = np.bincount(regions[mine & bracketed], minlength=count + 1)
    readings = []
    for territory, mask, depth, peak in found:
        part = walled == territory
        third = (
            signal_third(float(np.median(plane[part])), thirds) if part.any() else None
        )
        held, read = int(bracketed_count[territory]), int(readable_count[territory])
        wall = wall_sign(held, read)
        marrow = marrow_sign(third, *tags)
        readings.append(
            TerritoryReading(
                territory=territory,
                pixels=int(mask.sum()),
                walled_pixels=int(part.sum()),
                depth_mm=depth,
                peak_rc=(int(peak[0]), int(peak[1])),
                superior_mm=float(basis_lps[2] @ peak),
                signal_third=third,
                wall_share=held / read if read else float("nan"),
                border_edges=read,
                wall_sign=wall,
                marrow_sign=marrow,
                fat_sign=fat_sign(third, *tags),
                bone=bone_code(wall, marrow),
            )
        )
    return tuple(readings), walled


def assign_plane(
    plane: np.ndarray,
    reading: InteriorReading,
    spacing_rc: tuple[float, float],
    basis_lps: np.ndarray,
    thirds: tuple[float, float],
    tags: tuple[str, str],
    reach_mm: float,
) -> PlaneAssignment:
    """Ask every question of the plane's places and territories; keep every reading.

    `tags` is the series' (Fluid_Sensitive, Fat_Suppression) pair as the table gives it, and
    `thirds` its terciles above the background split (`RegimeKey.split_terciles`).
    """
    dark, available, labels = reading.dark, reading.available, reading.labels
    objects = np.zeros(plane.shape, dtype=np.int8)
    codes: dict[str, str] = {}
    margin = unrecorded(plane)
    recorded = available & ~margin
    edge = record_edge(margin, spacing_rc, reach_mm)
    seeded = labels > 0

    # AIR: measured low signal, outside the body's outline (the seeded tissue with its holes filled),
    # recorded, off the record's edge, in a field reaching deeper than a border window from the body.
    inside = ndi.binary_fill_holes(seeded)
    outside = recorded & ~inside
    open_dark = outside & dark & ~edge
    if seeded.any():
        depth = ndi.distance_transform_edt(~seeded, sampling=spacing_rc)
        parts, _ = ndi.label(open_dark, structure=np.ones((3, 3), dtype=bool))
        held = np.unique(parts[open_dark & (depth > reach_mm)])
        air = np.isin(parts, held[held > 0])
    else:
        air = np.zeros(plane.shape, dtype=bool)
    objects[air] = OBJECT_CODES["air"]
    codes["air"] = air_code(
        int(seeded.sum()),
        int(outside.sum()),
        int((outside & dark).sum()),
        int(open_dark.sum()),
        int(air.sum()),
    )

    # SKIN: the body's own above-split places that touch the air.
    touching = ndi.binary_dilation(air, structure=ndi.generate_binary_structure(2, 1))
    skin = inside & recorded & ~dark & touching
    objects[skin] = OBJECT_CODES["skin"]
    codes["skin"] = "identified" if skin.any() else "abstain_no_air"

    # BONES: every territory asked, over its walled part; FEMUR over TIBIA from the two deepest.
    compartment = compartments(dark, available, spacing_rc, reach_mm)
    inner, outer = edge_places(
        reading.edge_points_rc, reading.edge_normals_rc, plane.shape
    )
    readable = (
        ~np.isin(reading.edge_kinds, UNREADABLE_EDGES)
        & ~edge[inner[:, 0], inner[:, 1]]
        & ~edge[outer[:, 0], outer[:, 1]]
        & ~margin[outer[:, 0], outer[:, 1]]
    )
    readings, walled = territory_readings(
        plane, reading, readable, compartment, basis_lps, thirds, tags
    )
    unit = basis_lps / np.linalg.norm(basis_lps, axis=0)
    superior_in_plane = float(np.linalg.norm(unit[2]))
    ranked = sorted(readings, key=lambda r: r.depth_mm, reverse=True)
    bones = [r for r in ranked if r.bone in PAIR_CANDIDATES]
    open_deeper, stacked, crossed = 0, False, False
    if len(bones) >= 2:
        first, second = bones[0], bones[1]
        open_deeper = sum(
            r.depth_mm >= second.depth_mm
            and r.bone.startswith("abstain")
            and r.bone not in PAIR_CANDIDATES
            for r in ranked
        )
        stacked = (
            superior_share(basis_lps, first.peak_rc, second.peak_rc) >= HALF_TURN_SHARE
        )
        crossed = low_signal_between(dark, first.peak_rc, second.peak_rc)
    codes["pair"] = pair_code(
        superior_in_plane, len(bones), open_deeper, stacked, crossed
    )
    counts: dict[str, int] = {}
    femur = tibia = None
    if codes["pair"] == "femur_tibia":
        high, low = sorted(bones[:2], key=lambda r: r.superior_mm, reverse=True)
        femur, tibia = high.territory, low.territory
        # The marrow sign read place by place: under fat suppression a bright place is not marrow,
        # and where it runs on out of a bone's walled part it is fluid the territory took in.
        refused = place_signs(plane, thirds, tags, marrow_sign) < 0
        conflict = np.zeros(plane.shape, dtype=bool)
        for name, reading_of in (("femur", high), ("tibia", low)):
            part = walled == reading_of.territory
            fluid = taken_in(part, refused)
            bone = held_body(part & ~fluid, reading_of.peak_rc)
            conflict |= bone & (objects != 0)
            objects[bone & (objects == 0)] = OBJECT_CODES[name]
            counts[f"{name}_outside_walled"] = int(
                np.count_nonzero((labels == reading_of.territory) & ~part)
            )
            counts[f"{name}_refused_by_signal"] = int(np.count_nonzero(fluid))
            counts[f"{name}_cut_off"] = int(np.count_nonzero(part & ~fluid & ~bone))
        objects[conflict] = OBJECT_CODES["unassigned"]
        counts["conflict"] = int(conflict.sum())
        codes["femur"] = codes["tibia"] = "identified"
        # JOINT: the above-split places between the two along the leg's axis whose own signal
        # refuses fat.
        between = (
            between_along_superior(
                objects == OBJECT_CODES["femur"],
                objects == OBJECT_CODES["tibia"],
                basis_lps,
            )
            & recorded
            & (objects == 0)
        )
        above = between & ~dark
        fat_here = place_signs(plane, thirds, tags, fat_sign)
        verdicts = {f: joint_code(f) for f in (-1, 0, 1)}
        joint = above & np.isin(
            fat_here, [f for f, v in verdicts.items() if v == "joint"]
        )
        abstained = {
            v: int(np.count_nonzero(above & (fat_here == f)))
            for f, v in verdicts.items()
            if v != "joint"
        }
        objects[joint] = OBJECT_CODES["joint"]
        codes["joint"] = (
            "identified"
            if joint.any()
            else "abstain_between_without_fluid_signal"
            if above.any()
            else "abstain_nothing_between"
        )
        counts["between_low_signal"] = int(np.count_nonzero(between & dark))
        counts["between_fat_signal"] = abstained["abstain_fat_signal"]
        counts["between_signal_silent"] = abstained["abstain_signal_silent"]
    else:
        for name in ("femur", "tibia", "joint"):
            codes[name] = codes["pair"]
    for name, value in OBJECT_CODES.items():
        if name != "unassigned":
            counts[name] = int(np.count_nonzero(objects == value))
    counts["unrecorded"] = int(margin.sum())
    counts["record_edge"] = int(edge.sum())
    counts["outside_not_low_signal"] = int(np.count_nonzero(outside & ~dark))
    counts["outside_low_signal_not_air"] = int(np.count_nonzero(outside & dark & ~air))
    return PlaneAssignment(
        objects,
        margin,
        edge,
        inside,
        walled,
        readings,
        codes,
        counts,
        femur,
        tibia,
        superior_in_plane,
    )
