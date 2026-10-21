"""Bones found by their structure in the current study: the anchors (lane W9, SQUINT_TRAINING_BUILD §9).

**The question.** Where are the femur, the tibia, the patella and the fibula in THIS study, found by
what makes them bones and not by how much a rectangle resembles a stored case? Everything else is
placed from them (W10), so the bones are first.

**The rule is the established one, read at the cheapest scale that resolves it.** No new detector:
every identity below is the existing rule's, and every reading is an existing producer's.

1. Identity, on one bounded native plane per sagittal and coronal series: the middle slice's lens
   (`interior_regions`, inside the squint's own `lens_scope`), its field (`read_field`) and the
   established naming's bone blocks (`assign_plane`'s femur, tibia, joint and patella, nothing
   after them): the femur and the tibia are the deepest interior and the deepest one above or
   below it along the leg, the upper the femur; the patella the bone as bright as the femur in
   front of its lower end, on a fat-suppressed sagittal slice. Each slice is then
   read with the other sequence's slice of the same place (`with_partner`): a bone both name is kept
   where they agree. An axial series' middle slice is not read: the leg runs through it and the
   rule names no bone there.
2. Where each bone is most obvious, from cheap readings first. The femur's and the tibia's marrow
   body through the depth of each series without fat suppression (the bones' cheap profile: the
   squint's tiles, and 2 mm blocks of the bone's corridor only where the tiles cannot say). The
   key plane is the bootstrap's (`bone_key_planes`): the largest supported marrow body among the
   candidates the lens names as the bone (`name_territory`, against the carried places, with the
   marrow body as the second measurement). It is asked lazily, largest first, the next candidate
   only where a larger one is not named, as `knee.collapse.reference` describes ("only the planes
   the cheap reading points to are ever read in detail"); the middle slice is already named, so the
   answer is the same plane the bootstrap selects with fewer lens reads. The axial key plane of each bone
   is the largest scale-filtered 2 mm enclosed section its carried places touch
   (`scale_filtered_section`). The femur's breadth is the measured left-right span of those
   attributed axial sections, the bootstrap's own knee scale. The fibula is found as its rule finds
   it: the squint bounds its corridor, 2 mm blocks point to where a body could be
   (`fibula_pointer`), and the lens and `fibula_on_slice` run only on the planes they point to; its
   main slice is the plane where its region is largest. The patella's and the fibula's planes in
   the other views are the largest whole enclosed 2 mm sections their native sections, carried by
   place, seed (the coarse scouts).
3. One physical reference per bone from its three key planes (`StudyMap`, `reference_position`):
   complete only where all three are selected; a missing plane stays missing and no centroid fills
   it. A tie between distinct planes is named and never broken.
4. One leg, one set of objects (Law 9): each lens-named femur and tibia section is read against the
   same bone's sections of the other in-plane orientation, carried onto its slice by place
   (`places_on_slice`). Where the lens territory holding most of those places (`region_holding`)
   is not the one named the bone, the two views contradict each other and both are named a
   conflict; nothing is renamed or dropped, and the anchor's status says `conflict`. A patella
   named in front of a femur in conflict, and a fibula found against a tibia in conflict, carry the
   conflict on. (On two of the three studies first read, the middle-slice rule named the posterior
   soft tissue as the sagittal femur; the bootstrap holds the same sections.)

**What each territory is.** A bone's addressed support on one slice of one series, on the squint's
10 mm tile grid: the tiles its support covers (`ROLE_OBJECT`, with the measured share of each
tile's native pixels) and one tile round them (`ROLE_CONTEXT`). No tile is called outside the leg
here: that is the leg map's to say. The window is an address; the roles inside it are the
territory. The support behind it is kept (runtime only), with the cross-view checks it passed.

**Transcriptions, named for root to extract.** The runner's orchestration of the producers in step 2
lives in `scripts/run_interiors.py`, which the library must not import. The smallest faithful
transcriptions are here, each naming its source and pinned against it by the tests: `_name_bones`
(the bone blocks of `knee.objects.assignments.assign_plane`, whose later blocks cost about two
seconds on a 768 x 768 slice and name nothing the anchors read), `_thinned`
(`thinned`), `_bone_profile` (`bone_profile`), `_plane_windows` (`bone_plane_window_map`),
`_axial_sections` (the reading of `axial_bone_planes`), `_fibula_profile` and `_find_fibula`
(`fibula_profile`, `find_fibula` without a map), and `_scout` (`patella_key_planes`,
`fibula_key_planes`). Extracting them into `knee.collapse` would leave one copy for both callers.

**Known differences from the bootstrap, stated, not hidden.** The lens is read only on each bone's
strongest candidate plane, not on every pointed plane, so the leg that seeds the axial sections
gains only the confirmed key-plane sections; the patella's sagittal key plane is the middle slice
where its rule names it, not the through-depth patella read (`read_patella`), so it can lie a few
slices from the bootstrap's; and the patella's coronal and axial scouts are seeded by that one
section. Every refusal keeps its code; nothing unread is called absent.
"""

from __future__ import annotations

import math
import time
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass, field
from typing import Any

import numpy as np
from scipy import ndimage as ndi

from knee.collapse import relative as rel
from knee.collapse.bones import (
    IDENTIFIED,
    marrow_body,
    name_territory,
    tiles_around,
    tiles_touched,
)
from knee.collapse.coarse_section import (
    SECTION,
    body_axis_bounds_mm,
    coarse_depth,
    coarse_section,
    key_slices,
    scale_filtered_section,
)
from knee.collapse.noise import background_split, finite_values
from knee.collapse.physical import PlaneFrame
from knee.collapse.profile import (
    BlockReading,
    block_centres_rc,
    block_holds,
    block_medians,
    block_pixels,
    confirmations,
    could_hold_level_in_reach,
    footprint_reach,
    positive_runs,
    run_maxima,
)
from knee.collapse.squint_stack import SquintStack
from knee.collapse.study_map import StudyMap
from knee.diagnosis.squint_interfaces import (
    ANCHOR_SCHEMA,
    ROLE_CONTEXT,
    ROLE_OBJECT,
    TERRITORY_SCHEMA,
)
from knee.objects.assignments import (
    ALONG_THE_LEG,
    BONE_MM,
    FIBULA_POINTER_STATUS,
    LIGAMENT_SMOOTH_MM,
    LIKE_THE_TIBIA,
    OBJECT_CODES,
    Field,
    PlaneAssignment,
    along_the_leg,
    axes_in_plane,
    between_along_the_leg,
    carried_bone,
    fibula_code,
    fibula_corridor,
    fibula_on_slice,
    fibula_pointer,
    laid_by,
    main_slice,
    margin,
    marrow_light,
    pair_code,
    patella_code,
    patella_peak,
    patella_piece,
    places_from,
    places_on_slice,
    projected_places,
    read_field,
    region_holding,
    with_partner,
)
from knee.objects.interiors import (
    InteriorRegions,
    LensScope,
    full_frame_scope,
    interior_regions,
    lens_scope,
)
from knee.study.series import Series, selected_slice

PRODUCER = "knee.diagnosis.squint_anchors.find_anchors/v1"
BONES = ("femur", "tibia", "patella", "fibula")
# The lens's own settings, the proof run's (`scripts/run_interiors.py`, PROMINENCE_MM).
PROMINENCE_MM = 3.0
# The carried places on a lattice of half a finer block (`run_interiors.BONE_PLACES_STEP_MM`).
PLACES_STEP_MM = LIGAMENT_SMOOTH_MM / 2.0
NOT_READ = FIBULA_POINTER_STATUS["not_read"]
NONE = FIBULA_POINTER_STATUS["none"]
BODY = FIBULA_POINTER_STATUS["body"]
UNREADABLE = FIBULA_POINTER_STATUS["unreadable"]
CUT = FIBULA_POINTER_STATUS["cut"]
AXIAL_OVERLAP = "slice_within_the_other_bones_native_extent_not_attributed"
FIBULA_UNREADABLE = "abstain_fibula_corridor_unreadable"
CROSS_VIEW_CONFLICT = "the_other_views_section_lies_mostly_in_another_territory"


# -- the study's readings, made once for the call -------------------------------------------------
@dataclass
class _Cost:
    """What the call read: the native planes the lens read, the 2 mm block readings and the
    histograms, each with its address, and the seconds of each stage."""

    lens: list[dict] = field(default_factory=list)
    blocks: list[dict] = field(default_factory=list)
    splits: list[str] = field(default_factory=list)
    stages: dict[str, float] = field(default_factory=dict)

    def lens_plane(self, uid: str, z: int, purpose: str, window: Sequence[int]) -> None:
        r0, r1, c0, c1 = (int(v) for v in window)
        self.lens.append(
            {
                "series_uid": uid,
                "slice": int(z),
                "purpose": purpose,
                "window_rc": [r0, r1, c0, c1],
                "pixels": max(0, r1 - r0) * max(0, c1 - c0),
            }
        )

    def block_plane(
        self, uid: str, z: int, purpose: str, reading: BlockReading
    ) -> None:
        r0, r1, c0, c1 = reading.window_rc
        self.blocks.append(
            {
                "series_uid": uid,
                "slice": int(z),
                "purpose": purpose,
                "window_rc": [int(r0), int(r1), int(c0), int(c1)],
                "pixels": int((r1 - r0) * (c1 - c0)),
            }
        )

    def summary(self, seconds: float) -> dict[str, Any]:
        lens_planes = {(row["series_uid"], row["slice"]) for row in self.lens}
        block_planes = {(row["series_uid"], row["slice"]) for row in self.blocks}
        return {
            "seconds": seconds,
            "stages_seconds": dict(self.stages),
            "native_planes_read": len(lens_planes | block_planes),
            "native_lens_planes": len(self.lens),
            "native_lens_pixels": int(sum(row["pixels"] for row in self.lens)),
            "block_readings": len(self.blocks),
            "block_reading_planes": len(block_planes),
            "block_reading_pixels": int(sum(row["pixels"] for row in self.blocks)),
            "background_histograms": len(self.splits),
            "lens_reads": list(self.lens),
            "scope": "one find_anchors call for the whole study, shared by its four anchors; "
            "the squint itself is the caller's input and is not counted",
        }


class _Series:
    """One series of the study as the squint route loaded it, with each per-slice reading made once
    for the call: frames, black margins, seen light, the squint's lens scopes, the background split
    and the coarse 2 mm planes."""

    def __init__(self, record: Mapping[str, Any], cost: _Cost) -> None:
        self.record = record
        self.cost = cost
        self.series: Series = record["native_series"]
        self.stack: SquintStack = record["stack"]
        self.uid = str(self.series.row.series_uid)
        self.orientation = str(self.series.row.anatomical_plane).strip().lower()
        self.view = [
            str(self.series.row.anatomical_plane),
            str(self.series.row.fluid_sensitive),
            str(self.series.row.fat_suppression),
        ]
        self.fat_suppressed = int(self.series.row.fat_suppression) == 1
        self.fluid_sensitive = int(self.series.row.fluid_sensitive) == 1
        volume = self.series.volume
        self.depth = 0 if volume is None else len(volume)
        index = selected_slice(self.depth, None)
        self.index = -1 if index is None else int(index)
        self.shape: tuple[int, int] = (
            (0, 0) if volume is None else tuple(int(v) for v in np.shape(volume[0]))
        )
        self._frames: dict[int, PlaneFrame | None] = {}
        self._margins: dict[int, np.ndarray] = {}
        self._seen: dict[int, tuple[np.ndarray, np.ndarray]] = {}
        self._scopes: dict[int, LensScope] = {}
        self._lenses: dict[int, InteriorRegions] = {}
        self._coarse: dict[int, tuple[BlockReading, np.ndarray]] = {}
        self._split: float | None = None
        self.knee = ""
        if 0 <= self.index < len(self.series.slices):
            header = getattr(self.series.slices[self.index], "header", None)
            self.knee = str(getattr(header, "Laterality", "") or "").strip()
        # what the middle slice's naming made, once it is read
        self.reading: InteriorRegions | None = None
        self.assignment: PlaneAssignment | None = None
        self.objects: np.ndarray | None = None
        self.codes: dict[str, str] = {}
        self.named: dict[str, int | None] = {}
        self.partner_code = "not_read"

    # one slice's frame, or None where its header does not read as one
    def frame(self, z: int) -> PlaneFrame | None:
        if z not in self._frames:
            geometry = self.series.geometry
            try:
                self._frames[z] = (
                    None
                    if geometry is None
                    else PlaneFrame.from_dicom(
                        geometry.position[z],
                        geometry.orientation[z],
                        geometry.spacing[z],
                    )
                )
            except (IndexError, ValueError):
                self._frames[z] = None
        return self._frames[z]

    def thickness(self, z: int) -> float | None:
        values = getattr(self.series, "slice_thickness_mm", ())
        if not 0 <= z < len(values) or values[z] is None:
            return None
        value = float(values[z])
        return value if math.isfinite(value) and value > 0 else None

    def plane(self, z: int) -> np.ndarray:
        assert self.series.volume is not None
        return self.series.volume[z]

    def margin(self, z: int) -> np.ndarray:
        if z not in self._margins:
            self._margins[z] = margin(self.plane(z))
        return self._margins[z]

    # one slice's stored light as float64 and the places it has none for (`seen_native`)
    def seen(self, z: int) -> tuple[np.ndarray, np.ndarray]:
        if z not in self._seen:
            raw = np.asarray(self.plane(z), dtype=np.float64)
            self._seen[z] = (raw, ~np.isfinite(raw) | self.margin(z))
        return self._seen[z]

    # the series' background split, read once over its whole volume (`background_split`)
    def split(self) -> float:
        if self._split is None:
            assert self.series.volume is not None
            self._split = float(background_split(finite_values(self.series.volume)))
            self.cost.splits.append(self.uid)
        return self._split

    # the squint's lens scope for one slice (`run_interiors.lens_scopes_of`)
    def scope(self, z: int) -> LensScope:
        if z not in self._scopes:
            stack = self.stack
            if stack.code != "present":
                scope = full_frame_scope(self.shape, reason=stack.why or stack.code)
            elif (
                stack.maximum.ndim != 3
                or stack.coverage.shape != stack.maximum.shape
                or stack.maximum.shape[0] != self.depth
            ):
                scope = full_frame_scope(
                    self.shape,
                    reason="squint tile arrays do not match the series depth",
                )
            else:
                try:
                    scope = lens_scope(
                        stack.maximum[z],
                        stack.coverage[z],
                        stack.bounds_rc,
                        self.split(),
                        self.shape,
                    )
                except ValueError as error:
                    scope = full_frame_scope(
                        self.shape,
                        reason=f"invalid squint scope inputs: {error}",
                        tile_shape=np.shape(stack.maximum[z]),
                    )
            self._scopes[z] = scope
        return self._scopes[z]

    # the lens on one slice inside the squint's scope, once per slice (`run_interiors.lens_of`,
    # no borders): a part's own slice that is the middle slice is handed the middle's reading
    def lens(self, z: int, purpose: str) -> InteriorRegions:
        if z not in self._lenses:
            frame = self.frame(z)
            assert frame is not None
            plane = self.plane(z)
            scope = self.scope(z)
            self._lenses[z] = interior_regions(
                plane,
                frame.spacing_rc,
                self.split(),
                PROMINENCE_MM,
                available=np.isfinite(plane),
                scope=scope,
            )
            self.cost.lens_plane(self.uid, z, purpose, scope.window_rc)
        return self._lenses[z]

    # the shared coarse 2 mm plane: block medians and enclosed depth (`coarse_axial_blocks/depth`)
    def coarse(self, z: int, purpose: str) -> tuple[BlockReading, np.ndarray]:
        if z not in self._coarse:
            frame = self.frame(z)
            assert frame is not None
            plane = np.asarray(self.plane(z), dtype=np.float64)
            reading = block_medians(
                plane,
                self.margin(z) | ~np.isfinite(plane),
                frame.spacing_rc,
                float(LIGAMENT_SMOOTH_MM),
            )
            depth = coarse_depth(reading.median, self.fat_suppressed)
            self._coarse[z] = (reading, depth)
            self.cost.block_plane(self.uid, z, purpose, reading)
        return self._coarse[z]


# -- step 1: identity on the middle slice ---------------------------------------------------------
def _name_bones(
    plane: np.ndarray,
    reading: InteriorRegions,
    basis_lps: np.ndarray,
    fat_suppressed: bool,
    outside_picture: np.ndarray,
    field: Field,
) -> PlaneAssignment:
    """The bones of one slice as the established naming names them: its FEMUR and TIBIA, the JOINT
    between them, and its PATELLA, nothing else. TRANSCRIPTION of the first three blocks of
    `knee.objects.assignments.assign_plane`, which every later block of it names only outside
    (menisci and ligaments are low signal, the rest is placed where nothing is named), so these
    masks and codes are that function's own; `tests/test_squint_anchors.py` pins them against it.
    The later parts (menisci, cartilage, the PCL's bands, fluid, pads, fat) are not read: on a
    768 x 768 slice they cost about two seconds the anchors would throw away."""
    labels = reading.labels
    objects = field.objects.copy()
    codes = dict(field.codes)
    peaks, in_plane = field.peaks, field.in_plane
    _sides_in_plane, front_in_plane, leg_in_plane = in_plane
    spacing_rc = np.linalg.norm(basis_lps, axis=0)
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
        joint = (
            between_along_the_leg(labels == femur, labels == tibia, basis_lps)
            & (objects == 0)
            & ~outside_picture
        )
        objects[joint] = OBJECT_CODES["joint"]
        codes["joint"] = "identified" if joint.any() else "abstain_nothing_between"
    femur_places = objects == OBJECT_CODES["femur"]
    peak = (
        patella_peak(peaks, femur_places, basis_lps)
        if front_in_plane and femur is not None
        else None
    )
    piece = np.zeros(plane.shape, dtype=bool)
    if peak is not None and fat_suppressed:
        light = marrow_light(plane, femur_places)
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
    return PlaneAssignment(
        objects, codes, peaks, femur, tibia, patella, None, None, in_plane
    )


def _name_middle(own: _Series) -> str:
    """The middle slice read and named by the established rule, or why not. Only a slice the leg
    runs in is read: the rule names no bone on an axial slice."""
    if own.series.volume is None:
        return "no_stacked_volume"
    if own.stack.code != "present":
        return f"squint_{own.stack.code}"
    frame = own.frame(own.index) if own.index >= 0 else None
    if frame is None:
        return "geometry_unreadable"
    if not axes_in_plane(frame.basis_lps)[2]:
        return "not_read_leg_runs_through_the_plane"
    plane = own.plane(own.index)
    reading = own.lens(own.index, "middle_slice_naming")
    outside = own.margin(own.index)
    field = read_field(plane, reading, frame.basis_lps, outside)
    assignment = _name_bones(
        plane, reading, frame.basis_lps, own.fat_suppressed, outside, field
    )
    own.reading, own.assignment = reading, assignment
    own.objects = np.asarray(assignment.objects).copy()
    own.codes = dict(assignment.codes)
    own.named = {
        "femur": assignment.femur,
        "tibia": assignment.tibia,
        "patella": assignment.patella,
    }
    return "read"


def _partner_of(readings: list[_Series], own: _Series) -> _Series | None:
    """The other sequence's series of the same plane, the first in the study's order
    (`run_interiors.partner_of`)."""
    for other in readings:
        if (
            other is not own
            and other.series.row.anatomical_plane == own.series.row.anatomical_plane
            and other.series.row.fat_suppression != own.series.row.fat_suppression
        ):
            return other
    return None


def _read_with_partner(own: _Series, partner: _Series) -> str:
    """One middle slice read with its partner's (`run_interiors.read_with_partner`): the slices'
    places matched once, the partner's own naming laid on, the bones kept where both agree."""
    assert own.assignment is not None and partner.assignment is not None
    own_frame, partner_frame = own.frame(own.index), partner.frame(partner.index)
    assert own_frame is not None and partner_frame is not None
    thickness = own.thickness(own.index)
    if thickness is None:
        return "no_slice_thickness"
    source = places_from(
        ~partner.margin(partner.index),
        partner_frame,
        own_frame,
        own.shape,
        thickness,
    )
    if source is None:
        return "not_the_same_place"
    assert own.reading is not None
    objects, codes = with_partner(
        own.assignment,
        own.reading.labels,
        own_frame.basis_lps,
        own.margin(own.index),
        laid_by(partner.assignment.objects, source),
        partner.assignment.codes,
    )
    own.objects, own.codes = objects, codes
    for name in ("femur", "tibia", "patella"):
        if codes.get(name) not in ("identified", "agreed_with_its_partner"):
            own.named[name] = None
    return "read_with_" + partner.uid


@dataclass
class _Leg:
    """The femur's and the tibia's places in the scanner's millimetres from the middle slices the
    leg runs in, as their partner reading left them, and the first native patella
    (`run_interiors.leg_of`; the notch is not needed here)."""

    femur: np.ndarray
    tibia: np.ndarray
    patella: np.ndarray


def _leg_of(readings: list[_Series]) -> _Leg:
    femur, tibia = [np.zeros((0, 3))], [np.zeros((0, 3))]
    patella = np.zeros((0, 3))
    for own in readings:
        if own.assignment is None or own.objects is None:
            continue
        frame = own.frame(own.index)
        assert frame is not None
        for name, found in (("femur", femur), ("tibia", tibia)):
            places = np.argwhere(own.objects == OBJECT_CODES[name]).astype(float)
            found.append(frame.to_patient(places))
        if not len(patella) and own.codes.get("patella") == "identified":
            places = np.argwhere(own.objects == OBJECT_CODES["patella"]).astype(float)
            patella = frame.to_patient(places)
    return _Leg(np.concatenate(femur), np.concatenate(tibia), patella)


# -- step 2a: the femur's and the tibia's key planes from their cheap profile ----------------------
def _thinned(points_lps: np.ndarray) -> np.ndarray:
    """The places of a bone on a lattice of `PLACES_STEP_MM`, one per cell, the cell's own corner.
    TRANSCRIPTION of `scripts/run_interiors.py::thinned`."""
    points = np.asarray(points_lps, dtype=np.float64).reshape(-1, 3)
    points = points[np.isfinite(points).all(axis=1)]
    if not len(points):
        return points
    cells = np.rint(points / PLACES_STEP_MM).astype(np.int64)
    low = cells.min(axis=0)
    span = [
        int(hi) - int(lo) + 1 for hi, lo in zip(cells.max(axis=0), low, strict=True)
    ]
    if span[0] * span[1] * span[2] >= 2**62:
        return np.unique(cells, axis=0) * PLACES_STEP_MM
    key = ((cells[:, 0] - low[0]) * span[1] + (cells[:, 1] - low[1])) * span[2] + (
        cells[:, 2] - low[2]
    )
    key = np.unique(key)
    rest, z = np.divmod(key, span[2])
    x, y = np.divmod(rest, span[1])
    cells = np.column_stack((x + low[0], y + low[1], z + low[2]))
    return cells * PLACES_STEP_MM


@dataclass
class _Profile:
    """A bone's cheap profile through depth (`run_interiors.BoneProfile`, the fields read here):
    each slice's status and supported marrow-body area (NaN not read, unreadable or cut; 0.0
    measured empty), the native window of its finer reading (-1 where none), and the body each read
    slice holds: on 2 mm blocks (`fine`) or, where the tiles confirmed it, on the tiles (`tiles`)."""

    status: np.ndarray
    area_mm2: np.ndarray
    window_rc: np.ndarray
    fine: dict[int, tuple[BlockReading, np.ndarray]]
    tiles: dict[int, np.ndarray]
    light: float


def _bone_profile(
    own: _Series, places: np.ndarray, others: np.ndarray, light: float
) -> _Profile:
    """One bone's marrow body through the series' depth without the lens. TRANSCRIPTION of
    `scripts/run_interiors.py::bone_profile` (no relation footprint, the `LIKE_THE_TIBIA` level),
    reading the same library measurements in the same order."""
    stack = own.stack
    depth = int(stack.median.shape[0])
    bounds = stack.bounds_rc
    shape = (int(bounds[..., 1].max()), int(bounds[..., 3].max()))
    tile_px = (bounds[..., 1] - bounds[..., 0]) * (bounds[..., 3] - bounds[..., 2])
    status = np.full(depth, NOT_READ, dtype=np.int8)
    area = np.full(depth, np.nan)
    window_rc = np.full((depth, 4), -1, dtype=np.int32)
    fine: dict[int, tuple[BlockReading, np.ndarray]] = {}
    tiles: dict[int, np.ndarray] = {}
    reach_of: dict[tuple[int, int], Any] = {}
    low, high = LIKE_THE_TIBIA
    anchored = bool(np.isfinite(light) and light > 0)
    for z in range(depth):
        frame = own.frame(z)
        if frame is None:
            status[z] = UNREADABLE
            continue
        foot = projected_places(places, frame, shape)
        if not foot.any():
            continue
        near = tiles_touched(foot, bounds)
        corridor = tiles_around(near)
        if not anchored:
            status[z] = UNREADABLE
            continue
        block = block_pixels(frame.spacing_rc, LIGAMENT_SMOOTH_MM)
        if block not in reach_of:
            reach_of[block] = footprint_reach(bounds, block)
        lows, highs = stack.minimum[z], stack.maximum[z]
        possible, blind = could_hold_level_in_reach(
            lows, highs, low * light, high * light, reach_of[block]
        )
        could = corridor & possible
        inside = (
            np.isfinite(lows)
            & np.isfinite(highs)
            & (lows >= low * light)
            & (highs <= high * light)
        )
        confirmed = corridor & inside
        if not could.any():
            if (corridor & blind).any():
                status[z] = UNREADABLE
            else:
                status[z], area[z] = NONE, 0.0
            continue
        other_foot = projected_places(others, frame, shape)
        if not (corridor & blind).any() and (could == confirmed).all():
            other_near = tiles_touched(other_foot, bounds)
            kept = carried_bone(ndi.label(could)[0], near)
            body = kept & ~other_near
            seen_px = float(np.nansum((stack.coverage[z] * tile_px)[body]))
            total = seen_px * float(np.prod(frame.spacing_rc))
            status[z], area[z] = (BODY, total) if total > 0 else (NONE, 0.0)
            tiles[z] = body
            continue
        plane, unseen = own.seen(z)
        rows, cols = plane.shape
        spacing = np.asarray(frame.spacing_rc)
        held = bounds[could]
        context = np.ceil(BONE_MM / spacing).astype(int)
        window = (
            max(0, int(held[:, 0].min()) - int(context[0])),
            min(rows, int(held[:, 1].max()) + int(context[0])),
            max(0, int(held[:, 2].min()) - int(context[1])),
            min(cols, int(held[:, 3].max()) + int(context[1])),
        )
        reading = block_medians(
            plane, unseen, frame.spacing_rc, LIGAMENT_SMOOTH_MM, window
        )
        own.cost.block_plane(own.uid, z, "bone_profile", reading)
        open_edge = np.zeros(reading.median.shape, dtype=bool)
        open_edge[0, :] = window[0] > 0
        open_edge[-1, :] = window[1] < rows
        open_edge[:, 0] |= window[2] > 0
        open_edge[:, -1] |= window[3] < cols
        got = marrow_body(
            reading.median,
            reading.block_mm,
            light,
            LIKE_THE_TIBIA,
            block_holds(foot, reading),
            block_holds(other_foot, reading),
            open_edge,
        )
        if got.cut:
            status[z] = CUT
        elif got.area_mm2 > 0:
            status[z], area[z] = BODY, got.area_mm2
        else:
            status[z], area[z] = NONE, 0.0
        window_rc[z] = window
        fine[z] = (reading, got.body)
    return _Profile(status, area, window_rc, fine, tiles, float(light))


def _block_pixels_mask(
    reading: BlockReading, blocks: np.ndarray, shape: tuple[int, int]
) -> np.ndarray:
    """A block body on the plane's own pixels: each block's pixels over its window
    (`run_interiors.body_pixels`)."""
    r0, r1, c0, c1 = reading.window_rc
    wide = np.repeat(
        np.repeat(np.asarray(blocks, dtype=bool), reading.block_px[0], axis=0),
        reading.block_px[1],
        axis=1,
    )
    found = np.zeros(shape, dtype=bool)
    found[r0:r1, c0:c1] = wide[: r1 - r0, : c1 - c0]
    return found


def _plane_windows(
    profiles: Mapping[str, _Profile | str], z: int, shape: tuple[int, int]
) -> tuple[tuple[int, int, int, int], str]:
    """The native window a pointed plane's lens is read in: the union of both bones' profile
    windows on that slice, else the whole frame, named. TRANSCRIPTION of
    `scripts/run_interiors.py::bone_plane_window_map` for one slice."""
    rows, cols = shape
    boxes = []
    for bone in ("femur", "tibia"):
        profile = profiles.get(bone)
        if not isinstance(profile, _Profile) or not 0 <= z < len(profile.window_rc):
            continue
        r0, r1, c0, c1 = (int(v) for v in profile.window_rc[z])
        if (r0, r1, c0, c1) == (-1, -1, -1, -1) or min(r0, r1, c0, c1) < 0:
            continue
        clipped = (
            max(0, min(rows, r0)),
            max(0, min(rows, r1)),
            max(0, min(cols, c0)),
            max(0, min(cols, c1)),
        )
        if clipped[0] < clipped[1] and clipped[2] < clipped[3]:
            boxes.append(clipped)
    if not boxes:
        return (0, rows, 0, cols), "full_frame_fallback_missing_profile_window"
    window = (
        min(b[0] for b in boxes),
        max(b[1] for b in boxes),
        min(b[2] for b in boxes),
        max(b[3] for b in boxes),
    )
    return window, "profile_window_union" if len(
        boxes
    ) == 2 else "profile_window_single"


@dataclass
class _KeyPlane:
    """One bone's selected plane in one series: the slice, its support for the map (the profile's
    area, or the section's), the named section on its pixels, how it was named, and the lens
    territories it was named on (for the cross-view check)."""

    slice: int
    support_mm2: float | None
    region: np.ndarray
    how: str
    scale: str
    reading_scope: tuple[int, int, int, int]
    labels: np.ndarray


def _largest_first(area: np.ndarray, candidates: set[int]) -> list[tuple[int, ...]]:
    """The candidates with a finite supported area, largest first, equal areas one group: the order
    in which the largest named candidate is found by asking the fewest planes. A candidate whose
    area is not finite (not read, unreadable, cut) is no key plane (`bone_key_planes`' `held`)."""
    values = np.asarray(area, dtype=np.float64)
    held = sorted(
        z for z in candidates if 0 <= z < len(values) and np.isfinite(values[z])
    )
    return [
        tuple(z for z in held if values[z] == level)
        for level in sorted({float(values[z]) for z in held}, reverse=True)
    ]


def _bone_key_planes(
    own: _Series,
    bone: str,
    places: np.ndarray,
    others: np.ndarray,
    profiles: Mapping[str, _Profile | str],
    pointed: Mapping[str, set[int]],
    lenses: dict[tuple[int, tuple[int, int, int, int]], tuple[np.ndarray, np.ndarray]],
    outcomes: list[dict],
) -> list[_KeyPlane]:
    """The bone's key plane(s) on one profiled series, the bootstrap's (`bone_key_planes` over
    `read_bone`'s pointed planes): the largest supported marrow body among the candidates the lens
    names as the bone, every tie kept. The candidates are each run of support's maximum, the slices
    beside a cut maximum, the other bone's pointed planes where this bone's profile read a fine
    body, and the middle slice, which the established rule has already named. They are asked
    largest first and the asking stops at the first area the lens names: the same answer as naming
    every pointed plane, with fewer lens reads."""
    profile = profiles[bone]
    assert isinstance(profile, _Profile)
    shape = own.shape
    area = profile.area_mm2
    middle = own.index
    candidates = (
        set(pointed[bone])
        | {middle}
        | {z for z in pointed.get(_other(bone), set()) if z in profile.fine}
    )
    for group in _largest_first(area, candidates):
        named: list[_KeyPlane] = []
        for z in group:
            if z == middle:
                assert own.objects is not None
                named.append(
                    _KeyPlane(
                        z,
                        float(area[z]),
                        own.objects == OBJECT_CODES[bone],
                        "middle_slice_named_by_the_established_rule",
                        "native",
                        own.scope(z).window_rc,
                        own.lens(z, "middle_slice_naming").labels,
                    )
                )
                continue
            frame = own.frame(z)
            if frame is None:
                outcomes.append(
                    _outcome(own, bone, z, "key_plane", "unreadable_geometry")
                )
                continue
            window, window_code = _plane_windows(profiles, z, shape)
            key = (z, window)
            if key not in lenses:
                # the established lens inside the shared profile window (`bone_local_lens_of`)
                r0, r1, c0, c1 = window
                raw = np.asarray(own.plane(z))[r0:r1, c0:c1].copy()
                crop = interior_regions(
                    raw,
                    frame.spacing_rc,
                    own.split(),
                    PROMINENCE_MM,
                    available=np.isfinite(raw),
                )
                own.cost.lens_plane(own.uid, z, "key_plane_confirmation", window)
                labels = np.zeros(shape, dtype=crop.labels.dtype)
                available = np.zeros(shape, dtype=bool)
                labels[r0:r1, c0:c1] = crop.labels
                available[r0:r1, c0:c1] = crop.available
                lenses[key] = (labels, available)
            labels, available = lenses[key]
            body = None
            if z in profile.fine:
                reading, blocks = profile.fine[z]
                body = _block_pixels_mask(reading, blocks, shape)
            naming = name_territory(
                labels,
                available,
                projected_places(places, frame, shape),
                projected_places(others, frame, shape),
                body,
            )
            outcomes.append(
                _outcome(own, bone, z, "key_plane_lens", f"{naming.code}:{window_code}")
            )
            if naming.code == IDENTIFIED:
                named.append(
                    _KeyPlane(
                        z,
                        float(area[z]),
                        naming.region,
                        "strongest_profile_plane_named_by_the_lens",
                        "native",
                        window,
                        labels,
                    )
                )
        if named:
            return named
    # no named candidate holds a finite area: the bootstrap offers what is named, unmeasured
    if not np.isfinite(area[middle]):
        assert own.objects is not None
        return [
            _KeyPlane(
                middle,
                None,
                own.objects == OBJECT_CODES[bone],
                "middle_slice_named_profile_area_unread",
                "native",
                own.scope(middle).window_rc,
                own.lens(middle, "middle_slice_naming").labels,
            )
        ]
    return []


def _other(bone: str) -> str:
    return "tibia" if bone == "femur" else "femur"


def _outcome(own: _Series, bone: str, z: int | None, stage: str, code: str) -> dict:
    return {
        "bone": bone,
        "series_uid": own.uid,
        "orientation": own.orientation,
        "slice": None if z is None else int(z),
        "stage": stage,
        "code": code,
    }


# -- step 2b: the axial sections of the femur and the tibia --------------------------------------
@dataclass
class _AxialRead:
    """One axial series' scale-filtered sections: each bone's area per slice (NaN where none),
    the estimate bodies and the readings they lie on, the statuses, and the femur's left-right
    bounds of every attributed section."""

    areas: dict[str, np.ndarray]
    bodies: dict[str, dict[int, np.ndarray]]
    statuses: dict[str, dict[str, int]]
    femur_bounds: dict[int, tuple[float, float]]


def _axial_sections(own: _Series, femur: np.ndarray, tibia: np.ndarray) -> _AxialRead:
    """The femur's and the tibia's whole 2 mm enclosed sections on an axial series, seeded by
    their carried places; a slice wholly within the other bone's extent along the leg is named and
    not attributed. TRANSCRIPTION of the reading in `scripts/run_interiors.py::axial_bone_planes`
    (records, packing and observations left out)."""
    bones = ("femur", "tibia")
    areas = {b: np.full(own.depth, np.nan) for b in bones}
    bodies: dict[str, dict[int, np.ndarray]] = {b: {} for b in bones}
    statuses: dict[str, dict[str, int]] = {b: {} for b in bones}
    femur_bounds: dict[int, tuple[float, float]] = {}
    places = {
        "femur": np.asarray(femur).reshape(-1, 3),
        "tibia": np.asarray(tibia).reshape(-1, 3),
    }
    femur_low = float(places["femur"][:, 2].min()) if len(places["femur"]) else None
    tibia_top = float(places["tibia"][:, 2].max()) if len(places["tibia"]) else None
    shape = own.shape
    for z in range(own.depth):
        frame = own.frame(z)
        thick = own.thickness(z)
        if frame is None or thick is None:
            continue
        centre = frame.to_patient(
            np.array([[shape[0] / 2.0, shape[1] / 2.0]], dtype=float)
        )[0, 2]
        half = float(thick) / 2.0
        allowed = {
            "femur": tibia_top is None or centre - half > tibia_top,
            "tibia": femur_low is None or centre + half < femur_low,
        }
        seeds = {
            b: places_on_slice(places[b], frame, shape, float(thick)) for b in bones
        }
        for b in bones:
            if seeds[b].any() and not allowed[b]:
                statuses[b][AXIAL_OVERLAP] = statuses[b].get(AXIAL_OVERLAP, 0) + 1
        active = {b: bool(seeds[b].any() and allowed[b]) for b in bones}
        if not any(active.values()):
            continue
        reading, depth = own.coarse(z, "axial_bone_sections")
        block_area = float(np.prod(reading.block_mm))
        marked = {b: block_holds(seeds[b], reading) for b in bones}
        for b in bones:
            if not active[b]:
                continue
            both = scale_filtered_section(
                depth,
                marked[b],
                block_area,
                reading.block_mm,
                BONE_MM,
                {_other(b): marked[_other(b)]},
            )
            status = both.estimate.status
            statuses[b][status] = statuses[b].get(status, 0) + 1
            if status == SECTION and both.estimate.body is not None:
                areas[b][z] = both.estimate.area_mm2
                bodies[b][z] = both.estimate.body
                if b == "femur":
                    bounds = body_axis_bounds_mm(
                        both.estimate.body, reading, frame, (1.0, 0.0, 0.0)
                    )
                    if bounds is not None:
                        femur_bounds[z] = bounds
    return _AxialRead(areas, bodies, statuses, femur_bounds)


# -- step 2c: the fibula -------------------------------------------------------------------------
@dataclass
class _FibulaProfile:
    status: np.ndarray
    area_mm2: np.ndarray


def _fibula_profile(
    own: _Series,
    tibia: np.ndarray,
    middle_rc: tuple[int, int],
    light: float,
    top_mm: float,
    middle_lps: np.ndarray,
    knee: str,
) -> _FibulaProfile:
    """The fibula's cheap profile through the depth: the squint's corridor tiles first, a 2 mm
    pointer only where they cannot exclude a body. TRANSCRIPTION of
    `scripts/run_interiors.py::fibula_profile` (whole depth, the fields read here)."""
    stack = own.stack
    depth = int(stack.median.shape[0])
    status = np.full(depth, NOT_READ, dtype=np.int8)
    area = np.full(depth, np.nan)
    reach_of: dict[tuple[int, int], Any] = {}
    low, high = LIKE_THE_TIBIA
    middle = np.zeros(tibia.shape, dtype=bool)
    middle[middle_rc] = True
    anchored = bool(np.isfinite(light) and light > 0)
    for z in range(depth):
        corridor = fibula_corridor(stack.centres_lps[z], top_mm, middle_lps, knee)
        if not corridor.any():
            continue
        frame = own.frame(z)
        if frame is None or not anchored:
            status[z] = UNREADABLE
            continue
        block = block_pixels(frame.spacing_rc, LIGAMENT_SMOOTH_MM)
        if block not in reach_of:
            reach_of[block] = footprint_reach(stack.bounds_rc, block)
        possible, unseen_tiles = could_hold_level_in_reach(
            stack.minimum[z],
            stack.maximum[z],
            low * light,
            high * light,
            reach_of[block],
        )
        could = corridor & possible
        if not could.any():
            if (corridor & unseen_tiles).any():
                status[z] = UNREADABLE
            else:
                status[z], area[z] = NONE, 0.0
            continue
        plane, unseen = own.seen(z)
        rows, cols = plane.shape
        spacing = np.asarray(frame.spacing_rc)
        bounds = stack.bounds_rc[could]
        reach = np.ceil(BONE_MM / spacing).astype(int)
        window = (
            max(0, int(bounds[:, 0].min()) - int(reach[0])),
            min(rows, int(bounds[:, 1].max()) + int(reach[0])),
            max(0, int(bounds[:, 2].min()) - int(reach[1])),
            min(cols, int(bounds[:, 3].max()) + int(reach[1])),
        )
        reading = block_medians(
            plane, unseen, frame.spacing_rc, LIGAMENT_SMOOTH_MM, window
        )
        own.cost.block_plane(own.uid, z, "fibula_profile", reading)
        centres = frame.to_patient(block_centres_rc(reading).reshape(-1, 2)).reshape(
            *reading.median.shape, 3
        )
        cut = np.zeros(reading.median.shape, dtype=bool)
        cut[0, :] = window[0] > 0
        cut[-1, :] = window[1] < rows
        cut[:, 0] = window[2] > 0
        cut[:, -1] = window[3] < cols
        point = fibula_pointer(
            reading.median,
            np.asarray(reading.block_mm),
            centres,
            block_holds(tibia, reading),
            block_holds(middle, reading),
            light,
            top_mm,
            middle_lps,
            knee,
            cut,
        )
        status[z], area[z] = point.status, point.area_mm2
    return _FibulaProfile(status, area)


@dataclass
class _FibulaFound:
    slice: int
    region: np.ndarray
    area_mm2: float
    planes: list[tuple[int, float]]
    places_lps: np.ndarray


def _find_fibula(own: _Series, outcomes: list[dict]) -> _FibulaFound | None:
    """The fibula on its main slice of one series without fat suppression, from the middle slice's
    tibia: the cheap profile points, the lens and the established rule (`fibula_on_slice`) run on
    the planes it points to, and the main slice is the one where the region is largest.
    TRANSCRIPTION of `scripts/run_interiors.py::find_fibula` without a map guide."""
    assert own.objects is not None and own.assignment is not None
    tibia = own.objects == OBJECT_CODES["tibia"]
    tibia_named = own.named.get("tibia") is not None and bool(tibia.any())
    code = fibula_code(own.knee, tibia_named, own.fat_suppressed, True)
    if code != "identified":
        outcomes.append(_outcome(own, "fibula", None, "fibula_rule", code))
        return None
    middle = own.frame(own.index)
    assert middle is not None
    top_mm = float(middle.to_patient(np.argwhere(tibia).astype(float))[:, 2].max())
    territory = own.named["tibia"]
    peak = next(p for p in own.assignment.peaks if p.territory == territory)
    middle_rc = (int(peak.peak_rc[0]), int(peak.peak_rc[1]))
    middle_lps = middle.to_patient(np.asarray([middle_rc], dtype=float))[0]
    plane = own.plane(own.index)
    light = float(np.median(np.asarray(plane)[tibia]))
    profile = _fibula_profile(
        own, tibia, middle_rc, light, top_mm, middle_lps, own.knee
    )
    runs = positive_runs(profile.area_mm2)
    maxima = run_maxima(profile.area_mm2, runs)
    confirm = confirmations(runs, maxima, profile.status, (CUT,))
    pointed = sorted({int(z) for peaks in maxima for z in peaks} | set(confirm))
    if not pointed:
        unresolved = np.isin(profile.status, (UNREADABLE, CUT)).any()
        why = (
            FIBULA_UNREADABLE
            if unresolved
            else fibula_code(own.knee, True, False, False)
        )
        outcomes.append(_outcome(own, "fibula", None, "fibula_profile", why))
        return None
    read_at: dict[int, tuple[np.ndarray, int | None, float, PlaneFrame]] = {}
    for z in pointed:
        frame = own.frame(z)
        if frame is None:
            outcomes.append(
                _outcome(own, "fibula", z, "fibula_lens", "unreadable_geometry")
            )
            continue
        labels = own.lens(z, "fibula_pointed_plane").labels
        rows, cols = np.indices(labels.shape)
        places_lps = frame.to_patient(
            np.column_stack((rows.ravel(), cols.ravel())).astype(float)
        ).reshape(*labels.shape, 3)
        found, found_area = fibula_on_slice(
            labels,
            np.asarray(own.plane(z), dtype=float),
            frame.spacing_rc[0] * frame.spacing_rc[1],
            places_lps,
            tibia,
            middle_lps,
            np.zeros(labels.shape, dtype=bool),
        )
        read_at[z] = (labels, found, found_area, frame)
        outcomes.append(
            _outcome(
                own,
                "fibula",
                z,
                "fibula_lens",
                "identified"
                if found is not None
                else "no_region_like_the_tibia_below_it",
            )
        )
    planes = sorted(read_at)
    chosen = main_slice([read_at[z][2] for z in planes])
    if chosen is None:
        outcomes.append(
            _outcome(
                own,
                "fibula",
                None,
                "fibula_rule",
                fibula_code(own.knee, True, False, False),
            )
        )
        return None
    main_z = planes[chosen]
    labels, found, found_area, frame = read_at[main_z]
    region = labels == found
    return _FibulaFound(
        main_z,
        region,
        float(found_area),
        [(z, float(read_at[z][2])) for z in planes if read_at[z][1] is not None],
        frame.to_patient(np.argwhere(region).astype(float)),
    )


# -- step 2d: the coarse scouts (patella coronal and axial, fibula axial) -------------------------
@dataclass
class _ScoutRead:
    areas: np.ndarray
    bodies: dict[int, np.ndarray]
    statuses: dict[str, int]


def _scout(
    own: _Series,
    sources: Sequence[tuple[np.ndarray, PlaneFrame, float]],
    other: Callable[[int, PlaneFrame, tuple[int, int], float], np.ndarray] | None,
    purpose: str,
) -> _ScoutRead:
    """The largest whole enclosed 2 mm section that native sections of another view seed on this
    series: a source reaches a slice only where that slice's slab meets the section's own voxel
    extent, and only an in-picture seed pixel is read. TRANSCRIPTION of the reading in
    `scripts/run_interiors.py::patella_key_planes` and `::fibula_key_planes` (`other` gives the
    blocks of a bone that refuse a shared section, the fibula's carried tibia)."""
    areas = np.full(own.depth, np.nan)
    bodies: dict[int, np.ndarray] = {}
    statuses: dict[str, int] = {}
    for z in range(own.depth):
        frame = own.frame(z)
        thick = own.thickness(z)
        if frame is None or thick is None or not sources:
            continue
        normal = frame.normal()
        offset = float(normal @ frame.origin_lps)
        target_half = thick / 2.0
        shape = own.shape
        seed = np.zeros(shape, dtype=bool)
        reached = False
        for points, source_frame, source_thickness in sources:
            source_half = 0.5 * (
                abs(float(normal @ source_frame.basis_lps[:, 0]))
                + abs(float(normal @ source_frame.basis_lps[:, 1]))
                + abs(float(normal @ source_frame.normal())) * source_thickness
            )
            held = np.abs(points @ normal - offset) <= (target_half + source_half)
            if not held.any():
                continue
            reached = True
            projected = frame.to_native(points[held])
            in_picture = (
                np.isfinite(projected).all(axis=1)
                & (projected[:, 0] >= -0.5)
                & (projected[:, 0] < shape[0] - 0.5)
                & (projected[:, 1] >= -0.5)
                & (projected[:, 1] < shape[1] - 0.5)
            )
            if in_picture.any():
                pixels = np.floor(projected[in_picture] + 0.5).astype(np.int64)
                seed[pixels[:, 0], pixels[:, 1]] = True
        if not reached or not seed.any():
            continue
        reading, depth = own.coarse(z, purpose)
        others = None
        if other is not None:
            others = {"other": block_holds(other(z, frame, shape, thick), reading)}
        result = coarse_section(
            depth,
            block_holds(seed, reading),
            float(np.prod(reading.block_mm)),
            others,
        )
        statuses[result.status] = statuses.get(result.status, 0) + 1
        if result.body is not None:
            areas[z] = result.area_mm2
            bodies[z] = result.body
    return _ScoutRead(areas, bodies, statuses)


# -- territories ---------------------------------------------------------------------------------
def _tile_shares(mask: np.ndarray, bounds: np.ndarray) -> np.ndarray:
    """The share of each squint tile's native pixels a support covers, (TR, TC), by one integral
    image (as `tiles_touched` counts them)."""
    held = np.asarray(mask, dtype=bool)
    total = np.zeros((held.shape[0] + 1, held.shape[1] + 1), dtype=np.int64)
    total[1:, 1:] = held.cumsum(axis=0).cumsum(axis=1)
    r0, r1, c0, c1 = (bounds[..., k] for k in range(4))
    counts = total[r1, c1] - total[r0, c1] - total[r1, c0] + total[r0, c0]
    pixels = (r1 - r0) * (c1 - c0)
    return np.where(pixels > 0, counts / np.maximum(pixels, 1), 0.0)


def _territory(
    study_uid: str,
    own: _Series,
    bone: str,
    z: int,
    support: np.ndarray,
    measured_scope: tuple[int, int, int, int],
    provenance: dict[str, Any],
    key_planes: Mapping[str, Any],
) -> dict[str, Any] | None:
    """One addressed support on the squint's tile grid: the tiles it covers (object, with their
    measured share) and one tile round them (context); None for an empty support. No tile is
    called outside the leg here: the squint's exterior-low scope is a work prior, not an air label
    (on a fat-suppressed coronal it reaches into marrow that runs to the picture's edge), so that
    role is the leg map's to give."""
    bounds = np.asarray(own.stack.bounds_rc)
    share = _tile_shares(support, bounds)
    objects = share > 0
    if not objects.any():
        return None
    rows, cols = (
        np.flatnonzero(objects.any(axis=1)),
        np.flatnonzero(objects.any(axis=0)),
    )
    tile_rows, tile_cols = objects.shape
    r0, r1 = max(0, int(rows[0]) - 1), min(tile_rows, int(rows[-1]) + 2)
    c0, c1 = max(0, int(cols[0]) - 1), min(tile_cols, int(cols[-1]) + 2)
    roles = np.full((1, r1 - r0, c1 - c0), ROLE_CONTEXT, dtype=np.int8)
    roles[0][objects[r0:r1, c0:c1]] = ROLE_OBJECT
    # outside the measured scope a tile's share was not measured: NaN, never zero
    m0, m1, n0, n1 = measured_scope
    measured = (
        (bounds[..., 0] >= m0)
        & (bounds[..., 1] <= m1)
        & (bounds[..., 2] >= n0)
        & (bounds[..., 3] <= n1)
    )
    values = np.where(measured | objects, share, np.nan).astype(np.float32)
    native = bounds[r0:r1, c0:c1]
    p0, p1 = int(native[..., 0].min()), int(native[..., 1].max())
    q0, q1 = int(native[..., 2].min()), int(native[..., 3].max())
    return {
        "schema": TERRITORY_SCHEMA,
        "study_uid": study_uid,
        "series_uid": own.uid,
        "subject": bone,
        "origin": "anchor_structure",
        "tile_window": [int(z), int(z) + 1, r0, r1, c0, c1],
        "roles": roles,
        "object_share": values[r0:r1, c0:c1][None, ...],
        "native_support": {
            "mask": np.asarray(support, dtype=bool)[p0:p1, q0:q1][None, ...].copy(),
            "slices": [int(z)],
            "offset_rc": (p0, q0),
        },
        "anchors": [],
        "relation": None,
        "key_planes": dict(key_planes),
        "provenance": {
            "producer": PRODUCER,
            "view": list(own.view),
            "slice": int(z),
            "support_pixels": int(np.count_nonzero(support)),
            "outside_leg_role": "not_given_here_the_leg_map_gives_it",
            "measured_scope_rc": [int(v) for v in measured_scope],
            **provenance,
        },
    }


# -- the whole call ------------------------------------------------------------------------------
def _map_plane(
    own: _Series, bone: str, z: int, reason: str, provenance: str
) -> rel.KeyPlane:
    """One series' slice as the key plane it would be, from that slice's own frame, its precision
    half the slice's thickness (`run_interiors.map_plane`)."""
    frame = own.frame(z)
    if frame is None:
        return rel.invalid_plane(
            bone,
            own.orientation,
            "frame_unavailable",
            series_uid=own.uid,
            slice=z,
            reason=reason,
            provenance=provenance,
        )
    thick = own.thickness(z)
    return rel.plane_of_frame(
        bone,
        own.orientation,
        series_uid=own.uid,
        slice=z,
        frame=frame,
        precision_mm=float("nan") if thick is None else thick / 2.0,
        reason=reason,
        provenance=provenance,
    )


def _sections_lps(
    own: _Series, z: int, region: np.ndarray
) -> tuple[np.ndarray, PlaneFrame, float] | None:
    frame = own.frame(z)
    thick = own.thickness(z)
    if frame is None or thick is None or not region.any():
        return None
    return frame.to_patient(np.argwhere(region).astype(float)), frame, float(thick)


def _usable(record: object) -> bool:
    if not isinstance(record, Mapping):
        return False
    native = record.get("native_series")
    stack = record.get("stack")
    return (
        isinstance(native, Series)
        and isinstance(stack, SquintStack)
        and native.volume is not None
        and np.ndim(native.volume) == 3
        and len(native.volume) > 0
        and native.geometry is not None
        and stack.code == "present"
    )


@dataclass
class _Section:
    """One lens-named section of the femur or the tibia on one slice, with the lens territories it
    was named on, and what the other view's sections of the same bone said of it."""

    bone: str
    own: _Series
    slice: int
    mask: np.ndarray
    labels: np.ndarray
    checks: list[dict] = field(default_factory=list)

    def places_lps(self) -> np.ndarray:
        frame = self.own.frame(self.slice)
        assert frame is not None
        return frame.to_patient(np.argwhere(self.mask).astype(float))

    @property
    def contradicted(self) -> bool:
        return any(check["outcome"] == CROSS_VIEW_CONFLICT for check in self.checks)


def _cross_view(sections: list[_Section]) -> None:
    """Law 9 between the in-plane views: each section of a bone is read against the same bone's
    sections of the other orientation, carried onto its slice by place (`places_on_slice`, within
    half the slice's thickness). The lens territory holding most of the carried places
    (`region_holding`) must be one named the bone; where it is another, the views contradict each
    other. No carried place on the slice, or none in a territory, is unknown, never agreement."""
    places = {id(section): section.places_lps() for section in sections}
    for a in sections:
        frame = a.own.frame(a.slice)
        thick = a.own.thickness(a.slice)
        for b in sections:
            if b.bone != a.bone or b.own.orientation == a.own.orientation:
                continue
            if frame is None or thick is None:
                outcome = "geometry_unreadable"
            else:
                carried = places_on_slice(places[id(b)], frame, a.own.shape, thick)
                if not carried.any():
                    outcome = "no_carried_place_on_this_slice"
                else:
                    holder = region_holding(a.labels, carried)
                    outcome = (
                        "carried_places_in_no_territory"
                        if not holder.any()
                        else "consistent"
                        if (holder & a.mask).any()
                        else CROSS_VIEW_CONFLICT
                    )
            a.checks.append(
                {
                    "against_series_uid": b.own.uid,
                    "against_orientation": b.own.orientation,
                    "against_slice": b.slice,
                    "outcome": outcome,
                }
            )


@dataclass
class _Pending:
    """One support waiting to become a territory once the map has chosen the key planes."""

    bone: str
    own: _Series
    slice: int
    support: np.ndarray
    scope: tuple[int, int, int, int]
    provenance: dict[str, Any]
    section: _Section | None = None


@dataclass
class _Call:
    """What one call gathers: the map the key planes are offered to, every outcome and named
    conflict by bone, the femur's and tibia's lens-named sections and the supports that become
    territories."""

    study_uid: str
    cost: _Cost
    smap: StudyMap
    outcomes: dict[str, list[dict]]
    pending: list[_Pending] = field(default_factory=list)
    sections: list[_Section] = field(default_factory=list)
    conflicts: dict[str, list[dict]] = field(
        default_factory=lambda: {bone: [] for bone in BONES}
    )

    def section_at(self, bone: str, own: _Series, z: int) -> _Section | None:
        return next(
            (
                s
                for s in self.sections
                if s.bone == bone and s.own is own and s.slice == z
            ),
            None,
        )

    def offer(
        self,
        bone: str,
        own: _Series,
        z: int,
        support: float | None,
        reason: str,
        provenance: str,
    ) -> None:
        self.smap.offer(
            bone,
            _map_plane(own, bone, z, reason, provenance),
            support,
            f"{provenance}:{own.uid}",
        )

    def refuse(self, bone: str, own: _Series, reason: str, provenance: str) -> None:
        self.smap.offer(
            bone,
            rel.unresolved_plane(
                bone, own.orientation, rel.REFUSED, reason=reason, provenance=provenance
            ),
            None,
            f"{provenance}:{own.uid}",
        )

    def keep(
        self,
        bone: str,
        own: _Series,
        z: int,
        support: np.ndarray,
        scope: tuple[int, int, int, int],
        provenance: dict[str, Any],
        labels: np.ndarray | None = None,
    ) -> None:
        """A support to become a territory; a lens-named femur or tibia section (`labels` given)
        is also kept for the cross-view check."""
        section = None
        if labels is not None:
            section = _Section(bone, own, int(z), support, labels)
            self.sections.append(section)
        self.pending.append(
            _Pending(bone, own, int(z), support, scope, provenance, section)
        )


def _identity(
    readings: list[_Series], call: _Call
) -> tuple[list[_Series], dict[str, str]]:
    """Step 1: every middle slice the leg runs in, named and read with its partner."""
    middle_codes = {own.uid: _name_middle(own) for own in readings}
    named = [own for own in readings if own.assignment is not None]
    for own in named:
        partner = _partner_of(named, own)
        own.partner_code = (
            "none_of_the_other_sequence"
            if partner is None
            else _read_with_partner(own, partner)
        )
    for own in readings:
        for bone in ("femur", "tibia", "patella"):
            code = own.codes.get(bone, middle_codes[own.uid])
            call.outcomes[bone].append(
                _outcome(own, bone, own.index, "middle_slice", code)
            )
    return named, middle_codes


def _femur_and_tibia(named: list[_Series], leg: _Leg, call: _Call) -> _Leg:
    """Step 2a: the middle slices' sections, and on each series without fat suppression the key
    plane from the cheap profile, named by the lens. Returns the leg refined by the confirmed
    key-plane sections (`refine_leg` over the planes read here)."""
    places = {"femur": leg.femur, "tibia": leg.tibia}
    thin = {bone: _thinned(value) for bone, value in places.items()}
    confirmed: dict[str, list[np.ndarray]] = {"femur": [], "tibia": []}
    for own in named:
        assert own.objects is not None
        for bone in ("femur", "tibia"):
            mask = own.objects == OBJECT_CODES[bone]
            if own.named.get(bone) is not None and mask.any():
                call.keep(
                    bone,
                    own,
                    own.index,
                    mask,
                    own.scope(own.index).window_rc,
                    {
                        "derivation": "middle_slice_named_by_the_established_rule",
                        "rule": "knee.objects.assignments.assign_plane, read with its partner "
                        "(with_partner)",
                        "middle_slice_code": own.codes.get(bone),
                        "partner": own.partner_code,
                        "scale": "native",
                    },
                    own.lens(own.index, "middle_slice_naming").labels,
                )
        if own.fat_suppressed:
            continue
        profiles: dict[str, _Profile | str] = {}
        for bone in ("femur", "tibia"):
            mask = own.objects == OBJECT_CODES[bone]
            if own.named.get(bone) is None or not mask.any():
                profiles[bone] = "bone_not_named_on_the_middle_slice"
            elif not len(places[bone]):
                profiles[bone] = "no_carried_places"
            else:
                light = float(np.median(np.asarray(own.plane(own.index))[mask]))
                profiles[bone] = _bone_profile(
                    own, thin[bone], thin[_other(bone)], light
                )
            if isinstance(profiles[bone], str):
                call.outcomes[bone].append(
                    _outcome(own, bone, None, "bone_profile", str(profiles[bone]))
                )
        pointed: dict[str, set[int]] = {}
        for bone, profile in profiles.items():
            if isinstance(profile, _Profile):
                runs = positive_runs(profile.area_mm2)
                maxima = run_maxima(profile.area_mm2, runs)
                pointed[bone] = {int(z) for peaks in maxima for z in peaks} | set(
                    confirmations(runs, maxima, profile.status, (CUT,))
                )
        lenses: dict[
            tuple[int, tuple[int, int, int, int]], tuple[np.ndarray, np.ndarray]
        ] = {}
        for bone in ("femur", "tibia"):
            if not isinstance(profiles[bone], _Profile):
                continue
            chosen = _bone_key_planes(
                own,
                bone,
                places[bone],
                places[_other(bone)],
                profiles,
                pointed,
                lenses,
                call.outcomes[bone],
            )
            if not chosen:
                call.outcomes[bone].append(
                    _outcome(
                        own, bone, None, "key_plane", "no_candidate_named_by_the_lens"
                    )
                )
                call.refuse(
                    bone,
                    own,
                    "no_candidate_named_by_the_lens",
                    "squint_anchors.bone_key_planes",
                )
            for plane in chosen:
                call.offer(
                    bone,
                    own,
                    plane.slice,
                    plane.support_mm2,
                    "strongest supported marrow body of the bone through depth, named by the lens",
                    "squint_anchors.bone_key_planes",
                )
                call.outcomes[bone].append(
                    _outcome(own, bone, plane.slice, "key_plane", plane.how)
                )
                if plane.slice == own.index:
                    continue
                frame = own.frame(plane.slice)
                assert frame is not None
                confirmed[bone].append(
                    frame.to_patient(np.argwhere(plane.region).astype(float))
                )
                call.keep(
                    bone,
                    own,
                    plane.slice,
                    plane.region,
                    plane.reading_scope,
                    {
                        "derivation": plane.how,
                        "rule": "the cheap marrow-body profile through depth (bone_profile), "
                        "largest first, named by the lens in the profile windows "
                        "(knee.collapse.bones.name_territory)",
                        "profile_area_mm2": plane.support_mm2,
                        "scale": plane.scale,
                    },
                    plane.labels,
                )
    return _Leg(
        np.concatenate([leg.femur, *confirmed["femur"]]),
        np.concatenate([leg.tibia, *confirmed["tibia"]]),
        leg.patella,
    )


def _axial_bones(
    axial: list[_Series], refined: _Leg, call: _Call
) -> tuple[float | None, str | None]:
    """Step 2b: the femur's and the tibia's axial key planes and the femur's measured breadth."""
    femur_bounds: list[tuple[str, int, tuple[float, float]]] = []
    for own in axial:
        got = _axial_sections(own, refined.femur, refined.tibia)
        for bone in ("femur", "tibia"):
            for status, count in sorted(got.statuses[bone].items()):
                call.outcomes[bone].append(
                    _outcome(own, bone, None, "axial_sections", f"{status}={count}")
                )
            keys = key_slices(got.areas[bone])
            if not keys:
                call.refuse(
                    bone,
                    own,
                    "no_scale_filtered_axial_section",
                    "squint_anchors.axial_sections",
                )
            for z in keys:
                area = float(got.areas[bone][z])
                call.offer(
                    bone,
                    own,
                    z,
                    area,
                    "largest scale-filtered whole 2 mm axial bone section estimate the carried "
                    "places touch (a lossy scale filter, not the cortex-enclosed section)",
                    "squint_anchors.axial_sections",
                )
                reading, _depth = own.coarse(z, "axial_bone_sections")
                call.keep(
                    bone,
                    own,
                    z,
                    _block_pixels_mask(reading, got.bodies[bone][z], own.shape),
                    reading.window_rc,
                    {
                        "derivation": "axial_scale_filtered_section_estimate",
                        "rule": "knee.collapse.coarse_section.scale_filtered_section on the "
                        "shared 2 mm blocks, seeded by the carried places",
                        "section_area_mm2": area,
                        "scale": "2mm_blocks",
                    },
                )
        femur_bounds += [(own.uid, z, b) for z, b in sorted(got.femur_bounds.items())]
    if not femur_bounds:
        return None, None
    low = min(b[0] for _, _, b in femur_bounds)
    high = max(b[1] for _, _, b in femur_bounds)
    if not high > low:
        return None, None
    where = "; ".join(
        f"{uid} slices {sorted(z for u, z, _ in femur_bounds if u == uid)}"
        for uid in sorted({u for u, _, _ in femur_bounds})
    )
    return float(high - low), (
        "measured_femur_ml_breadth: the patient LPS left-right span of the block corners of every "
        "attributed femur scale-filtered axial section estimate (a lossy scale filter, not a "
        f"cortex boundary); {where}; bounds_mm [{low:.6g}, {high:.6g}]"
    )


def _scouted(
    bone: str,
    own: _Series,
    got: _ScoutRead,
    purpose: str,
    reason: str,
    call: _Call,
    seeds_in_conflict: bool,
) -> None:
    """A scout's largest whole sections offered as key planes, each kept as a territory, saying
    whether a section it was seeded by is itself in conflict."""
    for status, count in sorted(got.statuses.items()):
        call.outcomes[bone].append(
            _outcome(own, bone, None, purpose, f"{status}={count}")
        )
    keys = key_slices(got.areas)
    if not keys:
        call.refuse(
            bone,
            own,
            f"no_competent_coarse_section:{purpose}",
            f"squint_anchors.{purpose}",
        )
    for z in keys:
        area = float(got.areas[z])
        call.offer(bone, own, z, area, reason, f"squint_anchors.{purpose}")
        reading, _depth = own.coarse(z, purpose)
        call.keep(
            bone,
            own,
            z,
            _block_pixels_mask(reading, got.bodies[z], own.shape),
            reading.window_rc,
            {
                "derivation": "coarse_scout_section",
                "rule": f"knee.collapse.coarse_section.coarse_section seeded by the native {bone} "
                "sections of another view, carried by their voxel extent",
                "section_area_mm2": area,
                "scale": "2mm_blocks",
                "seeded_by_a_section_in_conflict": seeds_in_conflict,
            },
        )


def _patella(named: list[_Series], readings: list[_Series], call: _Call) -> None:
    """The patella: native on a fat-suppressed sagittal middle slice, scouted on the coronal and
    axial series from that section."""
    sources = []
    in_conflict = False
    for own in named:
        assert own.objects is not None
        if own.codes.get("patella") != "identified":
            continue
        femur = call.section_at("femur", own, own.index)
        against = (
            "no_femur_section"
            if femur is None
            else "views_disagree"
            if femur.contradicted
            else "views_agree"
            if any(check["outcome"] == "consistent" for check in femur.checks)
            else "unchecked"
        )
        if against == "views_disagree":
            in_conflict = True
            call.conflicts["patella"].append(
                _outcome(
                    own,
                    "patella",
                    own.index,
                    "patella_rule",
                    "named_in_front_of_a_femur_whose_views_disagree",
                )
            )
        region = own.objects == OBJECT_CODES["patella"]
        frame = own.frame(own.index)
        assert frame is not None
        area = float(np.count_nonzero(region)) * float(np.prod(frame.spacing_rc))
        call.offer(
            "patella",
            own,
            own.index,
            area,
            "the middle slice where the established rule names the patella by its light",
            "squint_anchors.patella_middle",
        )
        call.keep(
            "patella",
            own,
            own.index,
            region,
            own.scope(own.index).window_rc,
            {
                "derivation": "middle_slice_named_by_the_established_rule",
                "rule": "knee.objects.assignments.assign_plane (patella_peak, patella_piece)",
                "section_area_mm2": area,
                "scale": "native",
                "femur_it_was_named_against": against,
            },
        )
        section = _sections_lps(own, own.index, region)
        if section is not None:
            sources.append(section)
    if not sources:
        call.outcomes["patella"].append(
            {
                "bone": "patella",
                "series_uid": None,
                "orientation": None,
                "slice": None,
                "stage": "patella_rule",
                "code": "no_native_patella_on_a_fat_suppressed_sagittal_middle_slice",
            }
        )
        return
    for own in readings:
        if own.orientation in ("coronal", "axial"):
            _scouted(
                "patella",
                own,
                _scout(own, sources, None, "patella_scout"),
                "patella_scout",
                "largest whole enclosed 2 mm section holding native sagittal patella location seeds",
                call,
                in_conflict,
            )


def _fibula(
    named: list[_Series], axial: list[_Series], refined: _Leg, call: _Call
) -> None:
    """The fibula: its rule on each series without fat suppression, scouted on the axial series
    from its main sections, refused where the section holds the carried tibia."""
    sources = []
    in_conflict = False
    for own in named:
        if own.fat_suppressed:
            continue
        found = _find_fibula(own, call.outcomes["fibula"])
        if found is None:
            continue
        tibia = call.section_at("tibia", own, own.index)
        against = (
            "no_tibia_section"
            if tibia is None
            else "views_disagree"
            if tibia.contradicted
            else "views_agree"
            if any(check["outcome"] == "consistent" for check in tibia.checks)
            else "unchecked"
        )
        if against == "views_disagree":
            in_conflict = True
            call.conflicts["fibula"].append(
                _outcome(
                    own,
                    "fibula",
                    found.slice,
                    "fibula_rule",
                    "found_against_a_tibia_whose_views_disagree",
                )
            )
        call.offer(
            "fibula",
            own,
            found.slice,
            found.area_mm2,
            "the fibula's main slice: the pointed plane where its region is largest",
            "squint_anchors.find_fibula",
        )
        call.keep(
            "fibula",
            own,
            found.slice,
            found.region,
            own.scope(found.slice).window_rc,
            {
                "derivation": "fibula_main_slice_named_by_the_established_rule",
                "rule": "knee.objects.assignments.fibula_on_slice on the planes the cheap fibula "
                "profile points to (fibula_corridor, fibula_pointer)",
                "section_area_mm2": found.area_mm2,
                "resolved_planes": [[z, a] for z, a in found.planes],
                "scale": "native",
                "tibia_it_was_found_against": against,
            },
        )
        call.outcomes["fibula"].append(
            _outcome(own, "fibula", found.slice, "fibula_rule", "identified")
        )
        section = _sections_lps(own, found.slice, found.region)
        if section is not None:
            sources.append(section)

    def carried_tibia(
        z: int, frame: PlaneFrame, shape: tuple[int, int], thick: float
    ) -> np.ndarray:
        return places_on_slice(refined.tibia, frame, shape, thick)

    for own in axial:
        if not sources:
            call.outcomes["fibula"].append(
                _outcome(
                    own, "fibula", None, "fibula_scout", "no_native_fibula_sections"
                )
            )
            continue
        _scouted(
            "fibula",
            own,
            _scout(own, sources, carried_tibia, "fibula_scout"),
            "fibula_scout",
            "largest whole enclosed 2 mm section holding native sagittal/coronal fibula location "
            "seeds, refused where it holds the carried tibia's blocks",
            call,
            in_conflict,
        )


def _anchor(
    bone: str,
    call: _Call,
    territories: list[dict],
    breadth: tuple[float | None, str | None],
    knee: str,
    summary: dict[str, Any],
    provenance: dict[str, Any],
) -> dict[str, Any]:
    """One bone's anchor from the map: its key planes, its reference only where three planes are
    selected, its status and every outcome."""
    position = call.smap.positions()[bone]
    selected = {o: call.smap.selected(bone, o) for o in rel.ORIENTATIONS}
    conflicts = [
        {
            "stage": "key_plane_selection",
            "orientation": o,
            "code": plane.outcome,
            "candidates": [list(c) for c in plane.candidates],
        }
        for o, plane in selected.items()
        if plane.outcome == rel.TIED
    ] + list(call.conflicts[bone])
    if bone in ("femur", "tibia"):
        # both sequences named the bone on one place and their sections share no place
        conflicts += [
            row
            for row in call.outcomes[bone]
            if row["stage"] == "middle_slice"
            and row["code"] == "abstain_the_two_slices_disagree"
        ]
    # contradictory evidence is never one confident sum: a named conflict sets the status, and
    # the geometric reference of the selected planes is still given beside it
    if conflicts:
        status = "conflict"
    elif position.complete:
        status = "complete"
    elif territories or any(plane.usable for plane in selected.values()):
        status = "partial"
    else:
        status = "unavailable"
    point = (
        None if position.point_lps is None else [float(v) for v in position.point_lps]
    )
    return {
        "schema": ANCHOR_SCHEMA,
        "study_uid": call.study_uid,
        "subject": bone,
        "status": status,
        "territories": territories,
        "key_planes": {o: plane.address() for o, plane in selected.items()},
        "reference_lps": point,
        "reference": {
            "status": position.status,
            "geometry": position.geometry,
            "point_lps": point,
            "precision_mm": None
            if position.precision_mm is None
            else [float(v) for v in position.precision_mm],
            "line_direction": None
            if position.line_direction is None
            else [float(v) for v in position.line_direction],
            "problems": dict(position.problems),
            "rank": position.rank,
            "construction": "three_key_planes (knee.collapse.study_map.StudyMap); no centroid "
            "stands in for a missing plane",
        },
        "breadth_mm": breadth[0] if bone == "femur" else None,
        "breadth_source": breadth[1] if bone == "femur" else None,
        "conflicts": conflicts,
        "outcomes": list(call.outcomes[bone]),
        "knee": knee or None,
        "producer": PRODUCER,
        "cost": {**summary, "lens_reads": [dict(row) for row in summary["lens_reads"]]},
        "provenance": {
            **provenance,
            "candidate_planes": {
                o: [
                    {
                        "series_uid": c.plane.series_uid,
                        "slice": c.plane.slice,
                        "outcome": c.plane.outcome,
                        "support": c.support,
                        "source": c.source,
                    }
                    for c in call.smap.candidates.get((bone, o), [])
                ]
                for o in rel.ORIENTATIONS
            },
        },
    }


def find_anchors(study: Mapping[str, Any]) -> dict[str, dict[str, Any]]:
    """The femur, the tibia, the patella and the fibula of one study, found by their structure:
    one `knee.squint-anchor/v1` anchor per bone (the module note). `study` is what
    `knee.diagnosis.squint_profiles.read_study_squints` returns; its `native_series` are read, never
    changed, and nothing is kept after the call."""
    started = time.perf_counter()
    cost = _Cost()
    raw_series = study.get("series", ())
    records = list(raw_series) if isinstance(raw_series, Sequence) else []
    skipped = []
    readings = []
    for record in records:
        if _usable(record):
            readings.append(_Series(record, cost))
        else:
            skipped.append(
                {
                    "series_uid": record.get("series_uid")
                    if isinstance(record, Mapping)
                    else None,
                    "code": "series_unusable_no_native_volume_geometry_or_squint",
                }
            )
    knee = next((own.knee for own in readings if own.knee in ("R", "L")), "")
    call = _Call(
        str(study.get("study_uid", "")),
        cost,
        StudyMap(knee=knee or None, names=BONES),
        {bone: [] for bone in BONES},
    )

    clock = time.perf_counter()
    named, middle_codes = _identity(readings, call)
    leg = _leg_of(named)
    cost.stages["middle_naming_and_partner"] = time.perf_counter() - clock

    clock = time.perf_counter()
    refined = _femur_and_tibia(named, leg, call)
    cost.stages["femur_tibia_profiles_and_key_planes"] = time.perf_counter() - clock

    clock = time.perf_counter()
    _cross_view(call.sections)
    for section in call.sections:
        if section.contradicted:
            row = _outcome(
                section.own,
                section.bone,
                section.slice,
                "cross_view",
                CROSS_VIEW_CONFLICT,
            )
            row["against"] = [
                check
                for check in section.checks
                if check["outcome"] == CROSS_VIEW_CONFLICT
            ]
            call.conflicts[section.bone].append(row)
    cost.stages["cross_view"] = time.perf_counter() - clock

    axial = [
        own
        for own in readings
        if (frame := own.frame(own.index)) is not None
        and not axes_in_plane(frame.basis_lps)[2]
    ]
    clock = time.perf_counter()
    breadth = _axial_bones(axial, refined, call)
    cost.stages["axial_sections"] = time.perf_counter() - clock

    clock = time.perf_counter()
    _patella(named, readings, call)
    cost.stages["patella"] = time.perf_counter() - clock

    clock = time.perf_counter()
    _fibula(named, axial, refined, call)
    cost.stages["fibula"] = time.perf_counter() - clock

    # step 3: the territories, each told whether it lies on its bone's selected key plane
    territories: dict[str, list[dict]] = {bone: [] for bone in BONES}
    for item in call.pending:
        mine = call.smap.selected(item.bone, item.own.orientation)
        is_key = bool(
            mine.usable and mine.series_uid == item.own.uid and mine.slice == item.slice
        )
        built = _territory(
            call.study_uid,
            item.own,
            item.bone,
            item.slice,
            item.support,
            item.scope,
            {
                **item.provenance,
                "is_selected_key_plane": is_key,
                **(
                    {}
                    if item.section is None
                    else {
                        "cross_view": "views_disagree"
                        if item.section.contradicted
                        else "views_agree"
                        if any(
                            c["outcome"] == "consistent" for c in item.section.checks
                        )
                        else "unchecked",
                        "cross_view_checks": list(item.section.checks),
                    }
                ),
            },
            {
                item.own.orientation: {
                    "series_uid": item.own.uid,
                    "slice": item.slice,
                    "outcome": "selected" if is_key else "not_the_selected_key_plane",
                }
            },
        )
        if built is not None:
            territories[item.bone].append(built)
    summary = cost.summary(time.perf_counter() - started)
    provenance = {
        "skipped_series": skipped,
        "middle_slice_reads": middle_codes,
        "leg_places": {
            "femur": len(leg.femur),
            "tibia": len(leg.tibia),
            "patella": len(leg.patella),
            "femur_refined": len(refined.femur),
            "tibia_refined": len(refined.tibia),
        },
    }
    return {
        bone: _anchor(bone, call, territories[bone], breadth, knee, summary, provenance)
        for bone in BONES
    }


__all__ = ["BONES", "PRODUCER", "find_anchors"]
