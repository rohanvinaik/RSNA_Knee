"""Name the objects that are plain in the interiors' pictures: air, skin, femur, tibia and joint.

Each is named by what the pictures show, read off the interiors' own lenses:

- AIR: the measured low signal outside the leg, where it is a field, at least a centimetre thick.
  The leg is every territory, its holes filled. Measured on the proof study, 2026-10-14: the air
  fields are 2.5 to 5 cm thick, and the strips where the picture fades into its black margin are a
  few millimetres; those strips are not air.
- SKIN: the leg's places that touch the air.
- FEMUR and TIBIA: each is its own large territory, and they hold the strongest interior peaks, one
  above the other along the leg (Rohan, 2026-10-13, on the proof figure: «Good»). So: the territory
  with the deepest peak, and the deepest one above or below it. The upper is the femur.
- JOINT: what lies between the femur and the tibia, along the leg.
- PATELLA: the bone in front of the femur's lower end. Of the territories whose peak lies in front
  of the femur's, beside its lower end (within `PATELLA_REACH_MM` above the femur's lowest point),
  and that do not reach down past that point, the deepest. Seen on the proof's sagittal T1,
  2026-10-14: the patella is the oval bone there, with the femur's texture and bright marrow, and
  its own territory but for a thin strip of fat above it; on the fat-suppressed sagittal it shares
  a territory with the fat pad beneath it, which reaches down past the femur, so it is not named.

The leg runs along the patient's superior axis, and front to back along the anterior axis, both
read from the slice's own frame. Where the leg's axis does not lie in the plane (an axial slice),
the femur, tibia and joint are not named; where the front-back axis does not (a coronal slice),
the patella is not. The black
margin the reconstruction never filled is outside the picture, so nothing is named in it. Nothing
here draws; the run's renderer draws what this returns.
"""

from dataclasses import dataclass

import numpy as np
from scipy import ndimage as ndi

from knee.objects.interiors import InteriorReading

# More along the leg than across it: the cosine of 45 degrees. Geometry.
ALONG_THE_LEG = float(np.sqrt(0.5))
# Air around a leg is a field centimetres across; the picture's edge strips are millimetres.
AIR_FIELD_MM = 10.0
# The patella sits beside the femur's lower end, at the trochlea: its middle lies within a few
# centimetres above the joint. Claude's reading of the anatomy, 2026-10-14, not a sourced number.
PATELLA_REACH_MM = 50.0
OBJECT_CODES = {
    "unassigned": 0,
    "air": 1,
    "skin": 2,
    "femur": 3,
    "tibia": 4,
    "joint": 5,
    "patella": 6,
}
FOUR_NEIGHBOURS = ndi.generate_binary_structure(2, 1)


@dataclass(frozen=True, slots=True)
class Peak:
    """One territory's strongest interior peak: where it is, how deep, and how far superior."""

    territory: int
    depth_mm: float
    peak_rc: tuple[int, int]
    superior_mm: float


@dataclass(frozen=True, slots=True)
class PlaneAssignment:
    """The named objects (`OBJECT_CODES`), each object's code, and the peaks they were read from."""

    objects: np.ndarray
    codes: dict[str, str]
    peaks: tuple[Peak, ...]
    femur: int | None
    tibia: int | None
    patella: int | None


def margin(plane: np.ndarray) -> np.ndarray:
    """The black margin: stored zeros joined to the picture's frame through zeros."""
    zeros = plane == 0
    if not zeros.any():
        return zeros
    parts, _ = ndi.label(zeros)
    frame = np.concatenate((parts[0], parts[-1], parts[:, 0], parts[:, -1]))
    return np.isin(parts, frame[frame > 0])


def fields(outside: np.ndarray, spacing_rc: np.ndarray) -> np.ndarray:
    """The pieces of `outside` at least `AIR_FIELD_MM` thick (twice their deepest inner distance)."""
    parts, count = ndi.label(outside, structure=np.ones((3, 3), dtype=bool))
    if not count:
        return outside.copy()
    depth = ndi.distance_transform_edt(outside, sampling=spacing_rc)
    thickest = ndi.maximum(depth, parts, index=np.arange(1, count + 1))
    keep = np.flatnonzero(2.0 * np.asarray(thickest) >= AIR_FIELD_MM) + 1
    return np.isin(parts, keep)


def territory_peaks(
    labels: np.ndarray, distance_mm: np.ndarray, basis_lps: np.ndarray
) -> tuple[Peak, ...]:
    """Every territory's strongest interior peak, the deepest first."""
    found = []
    for territory in range(1, int(labels.max(initial=0)) + 1):
        mask = labels == territory
        if not mask.any():
            continue
        depth = float(distance_mm[mask].max())
        row, col = np.argwhere(mask & (distance_mm == depth))[0]
        superior = float(basis_lps[2] @ np.asarray((row, col), dtype=np.float64))
        found.append(Peak(territory, depth, (int(row), int(col)), superior))
    return tuple(sorted(found, key=lambda peak: peak.depth_mm, reverse=True))


def along_the_leg(basis_lps: np.ndarray, a_rc, b_rc) -> float:
    """How much of the way from a to b runs along the leg (the patient's superior axis), 0 to 1."""
    step = np.asarray(b_rc, dtype=np.float64) - np.asarray(a_rc, dtype=np.float64)
    way = basis_lps @ step
    length = float(np.linalg.norm(way))
    return abs(float(way[2])) / length if length else 0.0


def pair_code(leg_in_plane: bool, territories: int, partner_found: bool) -> str:
    """Whether the femur and tibia were named, or why not."""
    if not leg_in_plane:
        return "abstain_leg_runs_through_the_plane"
    if territories < 2:
        return "abstain_fewer_than_two_territories"
    if not partner_found:
        return "abstain_nothing_above_or_below_the_deepest"
    return "identified"


def patella_code(front_in_plane: bool, femur_named: bool, found: bool) -> str:
    """Whether the patella was named, or why not."""
    if not front_in_plane:
        return "abstain_front_runs_through_the_plane"
    if not femur_named:
        return "abstain_no_femur"
    if not found:
        return "abstain_nothing_in_front_of_the_femurs_lower_end"
    return "identified"


def patella_territory(
    labels: np.ndarray,
    peaks: tuple[Peak, ...],
    femur: int,
    tibia: int,
    basis_lps: np.ndarray,
) -> int | None:
    """The deepest territory in front of the femur, beside its lower end and not reaching past it."""
    rows, cols = np.indices(labels.shape)
    superior = basis_lps[2, 0] * rows + basis_lps[2, 1] * cols
    lowest = float(superior[labels == femur].min())
    femur_peak = next(peak for peak in peaks if peak.territory == femur)
    femur_front = float(basis_lps[1] @ np.asarray(femur_peak.peak_rc, dtype=np.float64))
    for peak in peaks:  # deepest first
        if peak.territory in (femur, tibia):
            continue
        front = float(basis_lps[1] @ np.asarray(peak.peak_rc, dtype=np.float64))
        in_front = (
            front < femur_front
        )  # anterior is the patient's minus-posterior direction
        beside = lowest < peak.superior_mm <= lowest + PATELLA_REACH_MM
        not_below = float(superior[labels == peak.territory].min()) > lowest
        if in_front and beside and not_below:
            return peak.territory
    return None


def between_along_the_leg(
    upper: np.ndarray, lower: np.ndarray, basis_lps: np.ndarray
) -> np.ndarray:
    """The places between `upper` and `lower` on each line along the leg, where both lie on it.

    The line is the pixel axis nearer the leg's axis; on it, the places after the last `upper`
    place and before the first `lower` place.
    """
    rows_axis = abs(basis_lps[2, 0]) >= abs(basis_lps[2, 1])
    a, b = (upper, lower) if rows_axis else (upper.T, lower.T)
    superior_step = basis_lps[2, 0] if rows_axis else basis_lps[2, 1]
    if superior_step > 0:  # superior lies toward larger indices: walk the other way
        a, b = a[::-1], b[::-1]
    index = np.arange(a.shape[0])[:, None]
    last_upper = np.where(a, index, -1).max(axis=0, initial=-1)
    first_lower = np.where(b, index, a.shape[0]).min(axis=0, initial=a.shape[0])
    both = (last_upper >= 0) & (first_lower < a.shape[0]) & (last_upper < first_lower)
    between = both & (index > last_upper) & (index < first_lower)
    if superior_step > 0:
        between = between[::-1]
    return between if rows_axis else between.T


def assign_plane(
    plane: np.ndarray, reading: InteriorReading, basis_lps: np.ndarray
) -> PlaneAssignment:
    """Name air, skin, femur, tibia and joint on one plane from its interiors reading."""
    dark, labels = reading.dark, reading.labels
    objects = np.zeros(plane.shape, dtype=np.int8)
    codes: dict[str, str] = {}
    outside_picture = margin(plane)

    # AIR: the low signal outside the leg, where it is a field. SKIN: the leg's places touching it.
    leg = ndi.binary_fill_holes(labels > 0)
    spacing_rc = np.linalg.norm(basis_lps, axis=0)
    air = fields(dark & ~leg & ~outside_picture, spacing_rc) & leg.any()
    objects[air] = OBJECT_CODES["air"]
    codes["air"] = (
        "identified"
        if air.any()
        else "abstain_no_leg"
        if not leg.any()
        else "abstain_no_field_outside_the_leg"
    )
    skin = leg & ndi.binary_dilation(air, structure=FOUR_NEIGHBOURS)
    objects[skin] = OBJECT_CODES["skin"]
    codes["skin"] = "identified" if skin.any() else "abstain_no_air"

    # FEMUR and TIBIA: the deepest territory, and the deepest one above or below it.
    peaks = territory_peaks(labels, reading.distance_mm, basis_lps)
    unit = basis_lps / np.linalg.norm(basis_lps, axis=0)
    leg_in_plane = float(np.linalg.norm(unit[2])) >= ALONG_THE_LEG
    partner = None
    if leg_in_plane and peaks:
        partner = next(
            (
                peak
                for peak in peaks[1:]
                if along_the_leg(basis_lps, peaks[0].peak_rc, peak.peak_rc)
                >= ALONG_THE_LEG
            ),
            None,
        )
    codes["femur"] = codes["tibia"] = codes["joint"] = pair_code(
        leg_in_plane, len(peaks), partner is not None
    )
    femur = tibia = None
    if partner is not None:
        upper, lower = sorted(
            (peaks[0], partner), key=lambda peak: peak.superior_mm, reverse=True
        )
        femur, tibia = upper.territory, lower.territory
        objects[labels == femur] = OBJECT_CODES["femur"]
        objects[labels == tibia] = OBJECT_CODES["tibia"]
        # JOINT: what lies between the two bones along the leg.
        joint = (
            between_along_the_leg(labels == femur, labels == tibia, basis_lps)
            & (objects == 0)
            & ~outside_picture
        )
        objects[joint] = OBJECT_CODES["joint"]
        codes["joint"] = "identified" if joint.any() else "abstain_nothing_between"

    # PATELLA: the bone in front of the femur's lower end.
    front_in_plane = float(np.linalg.norm(unit[1])) >= ALONG_THE_LEG
    patella = None
    if front_in_plane and femur is not None and tibia is not None:
        patella = patella_territory(labels, peaks, femur, tibia, basis_lps)
        if patella is not None:
            objects[(labels == patella) & (objects == 0)] = OBJECT_CODES["patella"]
    codes["patella"] = patella_code(
        front_in_plane, femur is not None, patella is not None
    )
    return PlaneAssignment(objects, codes, peaks, femur, tibia, patella)
