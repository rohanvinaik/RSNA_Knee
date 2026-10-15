"""Name the objects that are plain in the interiors' pictures, one at a time.

Each is named by what the pictures show, read off the interiors' own lenses:

- AIR: the measured low signal outside the leg, where it is a field, at least a centimetre thick.
  The leg is every territory, its holes filled. Measured on the proof study, 2026-10-14: the air
  fields are 2.5 to 5 cm thick, and the strips where the picture fades into its black margin are a
  few millimetres; those strips are not air.
- SKIN: the leg's places that touch the air.
- FEMUR and TIBIA: each is its own large territory, and they hold the strongest interior peaks, one
  above the other along the leg (Rohan, 2026-10-13, on the proof figure: «Good»). So: the territory
  with the deepest peak, and the deepest one above or below it. The upper is the femur.
- BONE MARROW: the inside of each bone named here. A bone's territory is its inside, within its
  dark shell, so the marrow needs no rule of its own.
- ARTICULAR CARTILAGE: the layer on each bone's joint surface, 2 to 3 mm thick where the femur's
  condyles meet the tibia's plateau. Seen on the proof's fat-suppressed coronal, 2026-10-14: down
  each column across the joint, the femur's marrow, its dark shell, a bright layer (x2.4 to x3.5
  of the marrow's light), the dark joint line, the tibia's bright layer, its shell, its marrow. So:
  on a coronal slice with fat suppression, in the joint, the places brighter than the bones' marrow
  by `CARTILAGE_BRIGHTER` within `CARTILAGE_MM` of a bone, named for the nearer bone, femoral or
  tibial (`cartilage_on`). Without fat suppression it is not brighter than marrow, so there it is
  laid on from the fat-suppressed slice of the same place (`with_partner`); the middle sagittal slice passes through
  the notch, where no joint surfaces meet, so it is not named there. Seen also on the proof: the
  bright fluid down the femur's outer side, and the lining of the notch's roof, lie in the joint
  within that reach and are named with it.
- JOINT: what lies between the femur and the tibia, along the leg.
- PATELLA: the bone in front of the femur's lower end, on a sagittal slice. Its marrow is the
  femur's tissue, so it is about as bright as the femur, and it has its own peak there. Seen on the
  proof's two middle sagittals, 2026-10-14 (the patella is plain to the eye in both): with fat
  suppression the patella is a solid oval as dark as the femur, and the fat pad below it is half
  again to two and a half times brighter, so its light parts them; without fat suppression the fat
  pad is as bright as marrow, and two territories meet across the patella's lower part, so there
  light and territory cannot part them. So: the deepest peak in front of the femur, no higher than
  `PATELLA_ABOVE_MM` above its lowest place (`patella_peak`); in that peak's territory, the places
  as bright as the femur, the piece of them holding most of the peak's own disc, its holes filled
  (`patella_piece`). Without fat suppression it is laid on from the fat-suppressed slice of the
  same place (`with_partner`).
- PCL: the posterior cruciate ligament, «thick, uniformly low-signal and curvilinear», from the
  femur's notch to the back of the tibia (docs/OBJECTS_AND_CONDITIONS.md). Seen on the proof's
  middle T2 sagittal, 2026-10-14: a thick dark band behind the femur's condyle curving down to the
  back of the tibia, x0.05 to x0.25 of the marrow's light; the low-signal lens marks only dots in
  it, the signal itself shows it whole. A ligament joins two bones. So: on a sagittal slice without
  fat suppression, the places whose light over `LIGAMENT_SMOOTH_MM` (uniformly dark, not speckled)
  is under `LIGAMENT_DARKER` of the femur's marrow, at least `LIGAMENT_THICK_MM` thick (the bones'
  thin shells drop out), the largest such piece that reaches within `SHELL_MM` of both the femur and
  the tibia (`ligament_joining`). With fat suppression the marrow is as dark as a ligament, so there
  it is laid on from the other slice of the same place. Seen also on the proof: it takes in some of
  the dark tissue around the band, and its last stretch down the back of the tibia stays with the
  dark tissue behind the tibia.
- MENISCI: on a coronal slice, the dark triangles at the two ends of the joint, between the femur's
  condyle and the tibia's plateau («an isosceles triangle on coronal images», low on every
  sequence: docs/OBJECTS_AND_CONDITIONS.md). So: the low signal with every part thinner than
  `MENISCUS_THICKNESS_MM` rubbed away (the bones' thin shells), the pieces of it that touch the
  joint, each whole, since a meniscus reaches out past the bones' ends, and the piece nearest each
  end, either side of the joint's middle. Seen on the proof's fat-suppressed coronal, 2026-10-14;
  on its T1 coronal the joint's dark band is not measured low signal, so nothing is named. The
  middle sagittal slice passes through the notch, where the joint holds the cruciate ligaments, so
  menisci are not named there.
  Which is MEDIAL and which LATERAL: the medial lies toward the other knee, so where the header
  names the knee (Laterality "R" or "L"; the proof study says "R"), the side follows from the
  patient's left axis. Where it does not, the menisci stay unsided.
- FIBULA: the bone under the tibia's outer back. Its head has the tibia's marrow, so it is as
  bright as the tibia, and it lies about 5 cm below the tibia's top (seen on the proof's T1 coronal
  and T2 sagittal, 2026-10-14; Rohan: «Do you not see the giant fucking bone that is the
  fibula?»). It is named on its main slice, as the method says: the squint points to where it must
  be (`fibula_block`: below the tibia's top, on the outer side); the interiors lens reads only that
  block on each slice that holds it; the fibula there is the region the lens already draws that
  looks like the tibia, well below its top and behind its middle, apart from the tibia and whole
  in the block (`fibula_on_slice`); and its main slice is the one where that region is largest.
  On a fat-suppressed sequence the marrow is darkened to the light of muscle, so it is not named
  there (`fibula_code`). Seen right on the proof's T2 sagittal, 2026-10-14: slice 30, the bone
  under the tibia's outer condyle, its head and neck.

TWO SLICES OF ONE PLACE (`with_partner`). A study images the knee in two sequences on the same
slices: on the proof, the two sagittals lie on the same planes within 0.002 mm and the two coronals
too, each pair at its own pixel size (measured through the import, 2026-10-14). It is one leg, so
an object found in one is the same object in the other (Rohan, 2026-10-14: «It's literally the same
leg, obviously the object would be the same in both views. That's the WHOLE thesis»), and each
sequence shows what the other may not («If it's visible in one lens but not the other (like "joint
fluid")...then great, we know how to find it, problem solved»). On the proof's
T1 coronal the joint's band is not dark enough for the low-signal lens, so the femur's and tibia's
territories run over the joint and its menisci; on its fat-suppressed coronal they do not. So a
slice is read with its partner, the other sequence's slice of the same place (`laid_on`): a bone
both name is named where both agree, and not at all where they share no place; a part only the
partner names is laid on from it, onto this slice's own interiors that nothing else holds, the
patella only where it holds this slice's own peak in front of the femur; and the joint is again
what lies between the bones.

The leg runs along the patient's superior axis, front to back along the anterior axis, and side to
side along the left axis, all read from the slice's own frame. Where the leg's axis does not lie in
the plane (an axial slice), the femur, tibia and joint are not named; where the side-to-side axis
does not (a sagittal slice), the menisci are not; where the front-to-back axis does not (a coronal
slice), the patella is not. The black margin the reconstruction never filled is outside the
picture, so nothing is named in it. Nothing here draws; the run's renderer draws what this returns.
"""

from dataclasses import dataclass

import numpy as np
from scipy import ndimage as ndi

from knee.objects.interiors import InteriorReading

# More along the leg than across it: the cosine of 45 degrees. Geometry.
ALONG_THE_LEG = float(np.sqrt(0.5))
# Air around a leg is a field centimetres across; the picture's edge strips are millimetres.
AIR_FIELD_MM = 10.0
# A bone's shell along the joint is about a millimetre thick; a meniscus is about 5 mm at its base.
# Claude's reading of the proof's fat-suppressed coronal, 2026-10-14.
MENISCUS_THICKNESS_MM = 2.0
# A bone is at least a centimetre across: a region smaller than a disc this wide is not one.
BONE_MM = 10.0
# The fibula's marrow is the tibia's tissue, so on one slice it is about as bright: within a
# quarter of the tibia's light. Its head lies under the tibia's plateau, at least 3 cm below the
# tibia's top. Claude's reading of the proof's T2 sagittal, 2026-10-14: the head is x1.00 to x1.08
# of the tibia's light and about 5 cm below its top; the muscle beside it is x0.1 to x0.6.
LIKE_THE_TIBIA = (0.75, 1.33)
FIBULA_BELOW_MM = 30.0
# The patella's marrow is the femur's tissue, so on one slice it is about as bright: within a
# quarter of the femur's light, as the fibula is of the tibia's. It rides on the femur's lower end
# and is about 5 cm tall, so its middle lies in front of the femur and no higher than 5 cm above the
# femur's lowest place on the slice. Claude's reading of the proof's fat-suppressed sagittal,
# 2026-10-14: the patella x0.75 to x1.33 of the femur's light, the fat pad below it x1.5 to x2.5;
# its peak 15 mm in front of the femur and 23 mm above the femur's lowest place.
LIKE_THE_FEMUR = (0.75, 1.33)
PATELLA_ABOVE_MM = 50.0
# Articular cartilage is 2 to 3 mm thick on the femoral condyles and the tibial plateau (anatomy);
# with fat suppression it is clearly brighter than the suppressed marrow beneath it. Claude's
# reading of the proof's fat-suppressed coronal, 2026-10-14: the cartilage x2.4 to x3.5 of the
# marrow's light, the marrow's own speckle within x0.7 to x1.3.
CARTILAGE_MM = 3.0
CARTILAGE_BRIGHTER = 1.5
# A ligament is «uniformly low-signal»: dark over a small area, not speckle by speckle, so its
# light is read as the median over 2 mm. The PCL is about 6 mm thick front to back (anatomy); a
# bone's dark shell is about a millimetre, so a band at least 3 mm thick is not a shell, and a
# ligament attached to a bone lies within 2 mm of its marrow. Claude's reading of the proof's T2
# sagittal, 2026-10-14: the PCL x0.05 to x0.25 of the marrow's light; the fat and fluid of the
# notch x0.5 to x1.4.
LIGAMENT_SMOOTH_MM = 2.0
LIGAMENT_DARKER = 0.3
LIGAMENT_THICK_MM = 3.0
SHELL_MM = 2.0
# What a slice's codes say when an object is named on it, by its own lens or with its partner's.
NAMED = ("identified", "agreed_with_its_partner", "laid_from_its_partner")
# A place of one slice that lies outside its partner's picture, where the partner has no say.
UNSEEN = -1
BONES = ("femur", "tibia")
MENISCI = ("meniscus", "medial_meniscus", "lateral_meniscus")
OBJECT_CODES = {
    "unassigned": 0,
    "air": 1,
    "skin": 2,
    "femur": 3,
    "tibia": 4,
    "joint": 5,
    "patella": 6,
    "meniscus": 7,
    "medial_meniscus": 8,
    "lateral_meniscus": 9,
    "fibula": 10,
    "femoral_cartilage": 11,
    "tibial_cartilage": 12,
    "pcl": 13,
}
CARTILAGES = ("femoral_cartilage", "tibial_cartilage")
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
    menisci: int
    patella: int | None = None


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


def meniscus_code(sides_in_plane: bool, joint_named: bool, found: int) -> str:
    """Whether menisci were named, or why not."""
    if not sides_in_plane:
        return "abstain_side_to_side_runs_through_the_plane"
    if not joint_named:
        return "abstain_no_joint"
    if not found:
        return "abstain_no_thick_low_signal_in_the_joint"
    return "identified"


def meniscus_side(knee: str, toward_left: bool) -> str:
    """Which meniscus a piece is: "medial", "lateral", or "meniscus" when the knee is not named.

    The medial meniscus lies on the side toward the other knee. For a right knee that is the
    patient's left; for a left knee, the patient's right. `knee` is the header's own word, "R" or
    "L"; `toward_left` says whether the piece is at the joint's end toward the patient's left.
    """
    if knee not in ("R", "L"):
        return "meniscus"
    return "medial" if toward_left == (knee == "R") else "lateral"


def side_code(knee: str, named: int) -> str:
    """Whether the menisci's sides were read, or why not."""
    if not named:
        return "abstain_no_meniscus"
    if knee not in ("R", "L"):
        return "abstain_header_names_no_knee"
    return "from_the_header"


def cartilage_code(
    sides_in_plane: bool, fat_suppressed: bool, joint_named: bool, found: bool
) -> str:
    """Whether the articular cartilage was named, or why not."""
    if not sides_in_plane:
        return "abstain_side_to_side_runs_through_the_plane"
    if not fat_suppressed:
        return "abstain_not_brighter_than_marrow_without_fat_suppression"
    if not joint_named:
        return "abstain_no_joint"
    if not found:
        return "abstain_nothing_bright_against_the_bones"
    return "identified"


def cartilage_on(
    plane: np.ndarray, objects: np.ndarray, spacing_rc: np.ndarray
) -> tuple[np.ndarray, np.ndarray]:
    """The articular cartilage on one slice, femoral and tibial: in the joint, the places brighter
    than the bones' marrow by `CARTILAGE_BRIGHTER`, within `CARTILAGE_MM` of the femur or the tibia,
    each named for the nearer bone. Both empty where the slice names no femur, tibia or joint."""
    femur = objects == OBJECT_CODES["femur"]
    tibia = objects == OBJECT_CODES["tibia"]
    joint = objects == OBJECT_CODES["joint"]
    none = np.zeros(plane.shape, dtype=bool)
    if not (femur.any() and tibia.any() and joint.any()):
        return none, none
    light = float(np.median(np.concatenate((plane[femur], plane[tibia]))))
    if light <= 0:
        return none, none
    to_femur = np.asarray(ndi.distance_transform_edt(~femur, sampling=spacing_rc))
    to_tibia = np.asarray(ndi.distance_transform_edt(~tibia, sampling=spacing_rc))
    bright = joint & (plane > CARTILAGE_BRIGHTER * light)
    femoral = bright & (to_femur <= CARTILAGE_MM) & (to_femur <= to_tibia)
    tibial = bright & (to_tibia <= CARTILAGE_MM) & (to_tibia < to_femur)
    return femoral, tibial


def pcl_code(
    front_to_back_in_plane: bool, fat_suppressed: bool, bones_named: bool, found: bool
) -> str:
    """Whether the PCL was named, or why not."""
    if not front_to_back_in_plane:
        return "abstain_front_to_back_runs_through_the_plane"
    if fat_suppressed:
        return "abstain_marrow_as_dark_as_a_ligament_with_fat_suppression"
    if not bones_named:
        return "abstain_no_femur_and_tibia"
    if not found:
        return "abstain_no_dark_band_joins_the_bones"
    return "identified"


def ligament_joining(
    plane: np.ndarray, objects: np.ndarray, spacing_rc: np.ndarray
) -> np.ndarray:
    """The thick, uniformly dark band joining the femur and the tibia: the places whose light over
    `LIGAMENT_SMOOTH_MM` is under `LIGAMENT_DARKER` of the femur's marrow, outside the bones and the
    black margin, at least `LIGAMENT_THICK_MM` thick; the largest piece of them reaching within
    `SHELL_MM` of both bones. Empty when no piece joins them."""
    femur = objects == OBJECT_CODES["femur"]
    tibia = objects == OBJECT_CODES["tibia"]
    none = np.zeros(plane.shape, dtype=bool)
    if not (femur.any() and tibia.any()):
        return none
    light = float(np.median(plane[femur]))
    if light <= 0:
        return none
    size = tuple(int(2 * round(LIGAMENT_SMOOTH_MM / step) + 1) for step in spacing_rc)
    uniform = ndi.median_filter(np.asarray(plane, dtype=np.float64), size=size)
    dark = (uniform < LIGAMENT_DARKER * light) & (plane > 0) & ~femur & ~tibia
    pieces, count = ndi.label(thick_parts(dark, spacing_rc, LIGAMENT_THICK_MM))
    if not count:
        return none
    near_femur = np.asarray(ndi.distance_transform_edt(~femur, sampling=spacing_rc))
    near_tibia = np.asarray(ndi.distance_transform_edt(~tibia, sampling=spacing_rc))
    labels = np.arange(1, count + 1)
    reach_femur = np.asarray(ndi.minimum(near_femur, pieces, index=labels))
    reach_tibia = np.asarray(ndi.minimum(near_tibia, pieces, index=labels))
    sizes = np.bincount(pieces.ravel(), minlength=count + 1)[1:]
    joining = (reach_femur <= SHELL_MM) & (reach_tibia <= SHELL_MM)
    if not joining.any():
        return none
    return pieces == int(labels[joining][np.argmax(sizes[joining])])


def patella_code(
    front_to_back_in_plane: bool,
    femur_named: bool,
    fat_suppressed: bool,
    peak_found: bool,
    found: bool,
) -> str:
    """Whether the patella was named by this slice's own light, or why not.

    Without fat suppression the fat pad under the patella is as bright as marrow, so light cannot
    part them; there the patella is laid on from the fat-suppressed slice of the same place
    (`with_partner`).
    """
    if not front_to_back_in_plane:
        return "abstain_front_to_back_runs_through_the_plane"
    if not femur_named:
        return "abstain_no_femur"
    if not fat_suppressed:
        return "abstain_fat_as_bright_as_marrow"
    if not peak_found:
        return "abstain_no_peak_in_front_of_the_femur"
    if not found:
        return "abstain_nothing_like_the_femur_at_its_peak"
    return "identified"


def patella_peak(
    peaks: tuple[Peak, ...], femur: np.ndarray, basis_lps: np.ndarray
) -> Peak | None:
    """The deepest peak in front of the femur, no higher than `PATELLA_ABOVE_MM` above the femur's
    lowest place: where the patella rides on the femur's lower end. None when there is none.

    Places are read along the patient's axes in the slice's own frame: y toward the back, z up.
    """
    at = np.argwhere(femur).astype(np.float64) @ basis_lps.T
    if not at.size:
        return None
    front, lowest = float(at[:, 1].min()), float(at[:, 2].min())
    for peak in peaks:  # the deepest first
        place = basis_lps @ np.asarray(peak.peak_rc, dtype=np.float64)
        if place[1] < front and lowest <= place[2] <= lowest + PATELLA_ABOVE_MM:
            return peak
    return None


def patella_piece(
    plane: np.ndarray,
    labels: np.ndarray,
    peak: Peak,
    light: float,
    spacing_rc: np.ndarray,
) -> np.ndarray:
    """The patella around its peak: in the peak's territory, the places within `LIKE_THE_FEMUR` of
    the femur's light `light`; of those pieces, the one holding most of the peak's own disc (the
    deepest the lens fits there, so one speckled place at the peak does not lose it); its holes
    filled. Empty when nothing there is as bright as the femur."""
    if light <= 0:
        return np.zeros(plane.shape, dtype=bool)
    low, high = LIKE_THE_FEMUR
    share = plane / light
    like = (labels == peak.territory) & (share >= low) & (share <= high)
    pieces, count = ndi.label(like, structure=FOUR_NEIGHBOURS)
    rows, cols = np.indices(plane.shape)
    r0, c0 = peak.peak_rc
    disc = ((rows - r0) * spacing_rc[0]) ** 2 + (
        (cols - c0) * spacing_rc[1]
    ) ** 2 <= peak.depth_mm**2
    held = np.bincount(pieces[disc & (pieces > 0)], minlength=count + 1)[1:]
    if not held.any():
        return np.zeros(plane.shape, dtype=bool)
    return ndi.binary_fill_holes(pieces == int(np.argmax(held)) + 1)


def fibula_block(
    centres_lps: np.ndarray,
    tibia_top_mm: float,
    tibia_middle_lps: np.ndarray,
    knee: str,
) -> np.ndarray:
    """The squint tiles where the fibula must be: below the tibia's top, on the knee's outer side of
    the tibia's middle. Empty when the header names no knee.

    Positions are the tiles' centres in the scanner's millimetres: x toward the patient's left, y
    toward the back, z up. The outer side is the patient's right for a right knee ("R") and the
    patient's left for a left one ("L").
    """
    if knee not in ("R", "L"):
        return np.zeros(centres_lps.shape[:-1], dtype=bool)
    across = centres_lps[..., 0] - tibia_middle_lps[0]
    outer = across < 0 if knee == "R" else across > 0
    below = centres_lps[..., 2] < tibia_top_mm
    return outer & below


def fibula_on_slice(
    labels: np.ndarray,
    plane: np.ndarray,
    pixel_mm2: float,
    places_lps: np.ndarray,
    tibia_before: np.ndarray,
    tibia_middle_lps: np.ndarray,
    cut: np.ndarray,
) -> tuple[int | None, float]:
    """On one slice's block, the fibula's territory and its area in square millimetres; (None, 0.0)
    when the block holds none.

    The fibula is the bone under the tibia's outer back that looks like the tibia. Of the regions
    the lens draws there, apart from the tibia and at least a disc `BONE_MM` across: those as
    bright as the tibia (within `LIKE_THE_TIBIA`), whose middle lies at least `FIBULA_BELOW_MM`
    below the tibia's top and behind the tibia's middle; the largest of them. The tibia on this
    slice is the region holding most of `tibia_before`, the tibia's places on the middle slice:
    anatomy is contiguous from slice to slice. A region the block's own edge cuts through (`cut`:
    the block's border where it is not the picture's edge) is not a whole object in view, so it is
    not the fibula; the fibula may run off the picture itself. `labels` and `plane` are the block's
    regions and light; `places_lps` (R, C, 3) its places in the scanner's millimetres, y toward
    the back, z up.
    """
    held = labels[tibia_before & (labels > 0)]
    if not held.size:
        return None, 0.0
    tibia_here = int(np.argmax(np.bincount(held)))
    tibia = labels == tibia_here
    light = float(np.median(plane[tibia]))
    top = float(places_lps[tibia][:, 2].max())
    least = np.pi * (BONE_MM / 2.0) ** 2
    low, high = LIKE_THE_TIBIA
    best, area = None, 0.0
    for territory in range(1, int(labels.max()) + 1):
        place = labels == territory
        size = float(np.count_nonzero(place)) * pixel_mm2
        if territory == tibia_here or size < least or size <= area or light <= 0:
            continue
        if (place & cut).any():
            continue
        middle = places_lps[place].mean(axis=0)
        like = low <= float(np.median(plane[place])) / light <= high
        below = top - float(middle[2]) >= FIBULA_BELOW_MM
        behind = float(middle[1]) > float(tibia_middle_lps[1])
        if like and below and behind:
            best, area = territory, size
    return best, area


def main_slice(areas: list[float]) -> int | None:
    """The slice where the object's region is largest; None when no slice holds it."""
    if not any(area > 0 for area in areas):
        return None
    return int(np.argmax(areas))


def fibula_code(knee: str, tibia_named: bool, fat_suppressed: bool, found: bool) -> str:
    """Whether the fibula was named, or why not.

    Marrow is mostly fat, so a fat-suppressed sequence darkens it to the light of muscle; there
    "as bright as the tibia" cannot tell bone from soft tissue, and the fibula is not named.
    """
    if knee not in ("R", "L"):
        return "abstain_header_names_no_knee"
    if not tibia_named:
        return "abstain_no_tibia"
    if fat_suppressed:
        return "abstain_marrow_suppressed_with_the_fat"
    if not found:
        return "abstain_no_bone_like_the_tibia_below_it"
    return "identified"


def thick_parts(
    mask: np.ndarray, spacing_rc: np.ndarray, thickness_mm: float
) -> np.ndarray:
    """`mask` with every part thinner than `thickness_mm` rubbed away (an opening by a disc)."""
    radius = thickness_mm / 2.0
    half = np.maximum(1, np.floor(radius / spacing_rc)).astype(int)
    rows, cols = np.mgrid[-half[0] : half[0] + 1, -half[1] : half[1] + 1]
    disc = (rows * spacing_rc[0]) ** 2 + (cols * spacing_rc[1]) ** 2 <= radius**2
    return ndi.binary_opening(mask, structure=disc)


def end_pieces(
    pieces: np.ndarray, count: int, across: np.ndarray, middle: float
) -> list[tuple[int, bool]]:
    """The piece nearest each end of the joint: the outermost piece on each side of its middle.

    `across` is each place's position toward the patient's left, and `middle` is the joint's
    middle on it. Each piece comes with whether its end is the one toward the patient's left.
    """
    if not count:
        return []
    labels = np.arange(1, count + 1)
    where = np.asarray(ndi.mean(across, pieces, index=labels))
    chosen = []
    for toward_left, side in ((False, where < middle), (True, where >= middle)):
        if side.any():
            outermost = np.where(side, np.abs(where - middle), -1.0)  # only this side's
            chosen.append((int(labels[int(np.argmax(outermost))]), toward_left))
    return chosen


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
    plane: np.ndarray,
    reading: InteriorReading,
    basis_lps: np.ndarray,
    knee: str = "",
    fat_suppressed: bool = False,
) -> PlaneAssignment:
    """Name air, skin, femur, tibia, joint, patella and menisci on one plane, from its interiors.

    `knee` is the header's own word for which knee the scan is, "R", "L" or blank; it sides the
    menisci. `fat_suppressed` is the series' own tag; only with it is the patella named by its
    light.
    """
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

    # PATELLA: on a fat-suppressed sagittal slice, the bone as bright as the femur at the deepest
    # peak in front of the femur's lower end.
    front_in_plane = float(np.linalg.norm(unit[1])) >= ALONG_THE_LEG
    femur_places = objects == OBJECT_CODES["femur"]
    peak = (
        patella_peak(peaks, femur_places, basis_lps)
        if front_in_plane and femur is not None
        else None
    )
    piece = np.zeros(plane.shape, dtype=bool)
    if peak is not None and fat_suppressed:
        light = float(np.median(plane[femur_places]))
        piece = patella_piece(plane, labels, peak, light, spacing_rc) & (objects == 0)
    codes["patella"] = patella_code(
        front_in_plane,
        femur is not None,
        fat_suppressed,
        peak is not None,
        bool(piece.any()),
    )
    patella = None
    if peak is not None and codes["patella"] == "identified":
        objects[piece] = OBJECT_CODES["patella"]
        patella = peak.territory

    # MENISCI: the thick low signal touching the joint, whole, the piece nearest each end.
    sides_in_plane = float(np.linalg.norm(unit[0])) >= ALONG_THE_LEG
    menisci = 0
    joint_places = objects == OBJECT_CODES["joint"]
    if sides_in_plane and joint_places.any():
        thick = thick_parts(dark & ~outside_picture, spacing_rc, MENISCUS_THICKNESS_MM)
        pieces, _ = ndi.label(thick)
        near_joint = ndi.binary_dilation(joint_places, structure=FOUR_NEIGHBOURS)
        touching = np.unique(pieces[near_joint & (pieces > 0)])
        pieces = np.where(np.isin(pieces, touching), pieces, 0)
        pieces, count = ndi.label(pieces > 0)
        rows, cols = np.indices(plane.shape)
        across = basis_lps[0, 0] * rows + basis_lps[0, 1] * cols  # mm toward the left
        middle = float(across[joint_places].mean())  # the joint's middle
        for piece, toward_left in end_pieces(pieces, count, across, middle):
            side = meniscus_side(knee, toward_left)
            name = "meniscus" if side == "meniscus" else f"{side}_meniscus"
            objects[pieces == piece] = OBJECT_CODES[name]
            menisci += 1
    codes["meniscus"] = meniscus_code(sides_in_plane, joint_places.any(), menisci)
    codes["meniscus_side"] = side_code(knee, menisci)

    # ARTICULAR CARTILAGE: on a fat-suppressed coronal slice, the bright layer on each bone, in the
    # joint.
    joint_named = codes["joint"] == "identified"
    femoral = tibial = np.zeros(plane.shape, dtype=bool)
    if sides_in_plane and fat_suppressed and joint_named:
        femoral, tibial = cartilage_on(plane, objects, spacing_rc)
    codes["cartilage"] = cartilage_code(
        sides_in_plane, fat_suppressed, joint_named, bool(femoral.any() or tibial.any())
    )
    objects[femoral] = OBJECT_CODES["femoral_cartilage"]
    objects[tibial] = OBJECT_CODES["tibial_cartilage"]

    # PCL: on a sagittal slice without fat suppression, the thick, uniformly dark band joining the
    # femur and the tibia.
    bones_named = femur is not None and tibia is not None
    pcl = np.zeros(plane.shape, dtype=bool)
    if front_in_plane and not fat_suppressed and bones_named:
        pcl = ligament_joining(plane, objects, spacing_rc)
        pcl &= np.isin(objects, (0, OBJECT_CODES["joint"]))
    codes["pcl"] = pcl_code(
        front_in_plane, fat_suppressed, bones_named, bool(pcl.any())
    )
    objects[pcl] = OBJECT_CODES["pcl"]
    return PlaneAssignment(objects, codes, peaks, femur, tibia, menisci, patella)


def laid_on(
    objects: np.ndarray,
    seen: np.ndarray,
    origin_lps: np.ndarray,
    basis_lps: np.ndarray,
    onto_origin_lps: np.ndarray,
    onto_basis_lps: np.ndarray,
    onto_shape: tuple[int, int],
    thickness_mm: float,
) -> np.ndarray | None:
    """One slice's named objects at the places of another slice of the same knee; None when the
    other slice is not the same place (some place of it lies more than half a slice thickness off
    this slice's plane).

    Each place of the other slice takes the object at this slice's nearest pixel, and `UNSEEN`
    where it lies outside this slice's picture: beyond its edge, or where `seen` is False (its
    black margin, which the reconstruction never filled). This slice has no say there. Frames are
    in the scanner's millimetres (DICOM LPS): a (3,) origin and the (3, 2) basis of rows and
    columns, spacing included.
    """
    rows, cols = np.indices(onto_shape)
    rc = np.column_stack((rows.ravel(), cols.ravel())).astype(np.float64)
    places = rc @ np.asarray(onto_basis_lps).T + np.asarray(onto_origin_lps)
    normal = np.cross(basis_lps[:, 0], basis_lps[:, 1])
    normal = normal / np.linalg.norm(normal)
    if float(np.abs((places - origin_lps) @ normal).max()) > thickness_mm / 2.0:
        return None
    native = np.rint((places - origin_lps) @ np.linalg.pinv(basis_lps).T).astype(int)
    inside = (
        (native[:, 0] >= 0)
        & (native[:, 0] < objects.shape[0])
        & (native[:, 1] >= 0)
        & (native[:, 1] < objects.shape[1])
    )
    inside[inside] = seen[native[inside, 0], native[inside, 1]]
    laid = np.full(rows.size, UNSEEN, dtype=objects.dtype)
    laid[inside] = objects[native[inside, 0], native[inside, 1]]
    return laid.reshape(onto_shape)


def with_partner(
    assignment: PlaneAssignment,
    labels: np.ndarray,
    basis_lps: np.ndarray,
    outside_picture: np.ndarray,
    laid: np.ndarray,
    partner_codes: dict[str, str],
) -> tuple[np.ndarray, dict[str, str]]:
    """One slice's named objects and codes, read with its partner's: the other sequence's slice of
    the same place (`laid`, the partner's objects at this slice's places, from `laid_on`).

    A bone both name is named where both agree, and where the partner's picture does not reach
    (`UNSEEN`: it has no say there); not at all where they share no place. A part only the partner
    names (the patella, the menisci, the cartilage, the PCL) is laid on from it, onto this slice's own
    interiors that nothing else holds; the patella only where it holds this slice's own peak in
    front of the femur, so the two lenses agree on where it is. The joint is then again what lies
    between the bones along the leg.
    """
    objects, codes = assignment.objects.copy(), dict(assignment.codes)
    for name in BONES:
        code = OBJECT_CODES[name]
        own, theirs = objects == code, laid == code
        if codes.get(name) in NAMED and partner_codes.get(name) in NAMED:
            agreed = own & (theirs | (laid == UNSEEN))
            objects[own & ~agreed] = 0
            codes[name] = (
                "agreed_with_its_partner"
                if agreed.any()
                else "abstain_the_two_slices_disagree"
            )
        elif partner_codes.get(name) in NAMED:
            placed = theirs & (labels > 0) & (objects == 0)
            objects[placed] = code
            if placed.any():
                codes[name] = "laid_from_its_partner"
    joint = OBJECT_CODES["joint"]
    objects[objects == joint] = 0
    femur, tibia = objects == OBJECT_CODES["femur"], objects == OBJECT_CODES["tibia"]
    between = np.zeros(objects.shape, dtype=bool)
    if femur.any() and tibia.any():
        between = between_along_the_leg(femur, tibia, basis_lps)
        between &= (objects == 0) & ~outside_picture
    objects[between] = joint
    if codes.get("joint") in NAMED or between.any():
        codes["joint"] = "identified" if between.any() else "abstain_nothing_between"
    for name, members in (
        ("patella", ("patella",)),
        ("meniscus", MENISCI),
        ("cartilage", CARTILAGES),
        ("pcl", ("pcl",)),
    ):
        if codes.get(name) in NAMED or partner_codes.get(name) not in NAMED:
            continue
        theirs = np.isin(laid, [OBJECT_CODES[member] for member in members])
        if name == "patella":
            peak = patella_peak(assignment.peaks, femur, basis_lps)
            if peak is None or not theirs[peak.peak_rc]:
                codes[name] = "abstain_the_two_slices_disagree"
                continue
        placed = theirs & (labels > 0) & np.isin(objects, (0, joint))
        objects[placed] = laid[placed]
        if placed.any():
            codes[name] = "laid_from_its_partner"
            if name == "meniscus":
                codes["meniscus_side"] = partner_codes.get("meniscus_side", "")
    return objects, codes
