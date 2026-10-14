"""One physical measurement pass over a loaded series; no anatomical assignments."""

from dataclasses import dataclass, field

import numpy as np

from knee.collapse.depth import DEFAULT_MINIMUM_VALID
from knee.collapse.physical import PlaneFrame, Squint, physical_squint
from knee.collapse.structure import StructureBars
from knee.compute.contracts import handed_on
from knee.objects.boundaries import BoundaryCensus, boundary_census
from knee.objects.interiors import InteriorReading, read_interiors
from knee.objects.profiles import ProfileReading, sample_profiles
from knee.study.series import Series, selected_slice
from knee.telemetry import ledger

#: The tile, in millimetres, the funnel squints at when a run names no request (the-funnel task
#: 1.1). Its provenance is `openspec/changes/the-funnel/design.md` §3: 8 mm, from the founder's
#: "16x16 grid" on "256x256" at about half a millimetre a pixel, the lead's arithmetic, and his
#: to change by eye. A request names its own `tile_mm`, validated below; this is the one value the
#: route reads when there is no request to ask, declared here beside the request and never inside
#: a body.
DEFAULT_TILE_MM: float = 8.0

#: The line-up's match bar when a run names no request (the-funnel task 3a.1): half the default
#: tile. Its provenance is `openspec/changes/the-funnel/design.md` §3, `half_tile_mm`: "a tile
#: centre nearer than half a tile is the same patch; the lead's", and his to change. A request
#: carries its own `half_tile_mm`, which defaults to half its own tile, validated below.
DEFAULT_HALF_TILE_MM: float = DEFAULT_TILE_MM / 2.0


@dataclass(frozen=True, slots=True)
class AnalysisRequest:
    """Explicit settings, never object admission bars.

    None selects floor(n/2) in Chapter 1's spatial stack order (`selected_slice`, the one rule,
    shared with the field's structural reading). Offsets run along the recorded in-plane unit
    patient vector, not the unprojected requested axis. Probe sites are native pixel-centres of
    all tiles, including remainder tiles. `structure_bars` are the field's structural reading's
    bars (task 7.1), every one an argument with its provenance in `StructureBars`.

    `half_tile_mm` is the line-up's match bar (the-funnel task 3a.1, `knee.collapse.lineup`): a
    partner tile centre nearer than this, in the scanner's millimetres, reads the same patch of
    knee as the recipient tile. None, the default, resolves to `tile_mm / 2` when the request is
    made, so the receipt always carries the number the run used. Provenance:
    `openspec/changes/the-funnel/design.md` §3 ("a tile centre nearer than half a tile is the
    same patch; the lead's"); the founder changes it. A bar that is not a finite positive number
    is refused by name, `invalid_half_tile_mm`.

    `minimum_valid` is the depth collapse's bar (the-funnel task 4.1, `knee.collapse.depth`):
    how many slices must carry a finite reading before a lens may stand at the slice where its
    reading peaks. None, the default, resolves to `knee.collapse.depth.DEFAULT_MINIMUM_VALID`
    when the request is made, so the receipt always carries the number the run used.
    Provenance: `openspec/changes/the-funnel/design.md` §3 ("a lens needs eight slices with a
    reading to stand anywhere; the lead's"); the founder changes it. A bar that is a bool, not
    an int, or negative is refused by name, `invalid_minimum_valid`.
    """

    tile_mm: float
    offsets_mm: tuple[float, ...]
    direction_lps: tuple[float, float, float]
    backend: str
    slice_index: int | None = None
    prominence_mm: float | None = None
    conversation: bool = False
    minimum_divide_sites: int = 1
    structure_bars: StructureBars = field(default_factory=StructureBars)
    half_tile_mm: float | None = None
    minimum_valid: int | None = None

    def __post_init__(self) -> None:
        if not np.isfinite(self.tile_mm) or self.tile_mm <= 0:
            raise ValueError("invalid_tile_mm")
        # The frozen dataclass's own setter refuses; the default is written once, here, so the
        # request carries the bar it was made with and `asdict` saves a number, never None.
        if self.half_tile_mm is None:
            object.__setattr__(self, "half_tile_mm", float(self.tile_mm) / 2.0)
        if (
            isinstance(self.half_tile_mm, bool)
            or not isinstance(self.half_tile_mm, (int, float))
            or not np.isfinite(self.half_tile_mm)
            or self.half_tile_mm <= 0
        ):
            raise ValueError("invalid_half_tile_mm")
        # The depth collapse's bar, written once the same way, so the receipt carries the
        # number the run stood its lenses under and never None.
        if self.minimum_valid is None:
            object.__setattr__(self, "minimum_valid", DEFAULT_MINIMUM_VALID)
        if (
            isinstance(self.minimum_valid, bool)
            or not isinstance(self.minimum_valid, int)
            or self.minimum_valid < 0
        ):
            raise ValueError("invalid_minimum_valid")
        offsets = np.asarray(self.offsets_mm, dtype=np.float64)
        if (
            offsets.ndim != 1
            or not np.all(np.isfinite(offsets))
            or np.any(np.diff(offsets) <= 0)
        ):
            raise ValueError("invalid_profile_offsets")
        direction = np.asarray(self.direction_lps, dtype=np.float64)
        if (
            direction.shape != (3,)
            or not np.all(np.isfinite(direction))
            or not np.isclose(direction @ direction, 1, atol=1e-12, rtol=0)
        ):
            raise ValueError("invalid_patient_direction")
        if self.backend not in ("reference", "jit"):
            raise ValueError("invalid_backend")
        if self.slice_index is not None and (
            type(self.slice_index) is not int or self.slice_index < 0
        ):
            raise ValueError("invalid_slice_index")
        if type(self.conversation) is not bool or (
            self.conversation and self.prominence_mm is None
        ):
            raise ValueError("invalid_conversation_request")
        if type(self.minimum_divide_sites) is not int or self.minimum_divide_sites < 0:
            raise ValueError("invalid_minimum_divide_sites")
        if self.prominence_mm is not None:
            if not np.isfinite(self.prominence_mm) or self.prominence_mm <= 0:
                raise ValueError("invalid_prominence_mm")
            if not len(offsets) or not np.any(offsets == 0):
                raise ValueError("invalid_border_offsets")


@dataclass(frozen=True, slots=True)
class SeriesMeasurement:
    code: str
    slice_index: int | None = None
    frame: PlaneFrame | None = None
    squint: Squint | None = None
    profiles: ProfileReading | None = None
    projection_norm: float | None = None
    acquired_plane: np.ndarray | None = None
    points_rc: np.ndarray | None = None
    normals_rc: np.ndarray | None = None
    validation_code: str | None = None
    source_plane: str | None = None
    orientation_spread: float | None = None
    interiors: InteriorReading | None = None
    slice_thickness_mm: float | None = None
    boundaries: BoundaryCensus | None = None


def measure_series(
    series: Series, request: AnalysisRequest, *, background_split: float = float("nan")
) -> SeriesMeasurement:
    """One measurement pass, with what it consumed and produced recorded by this stage itself.

    The consumer records consumption at the point of reading (`specs/route-composition`): the
    volume and geometry from Chapter 1, and the background split from the field.
    """
    ledger.record(
        "study.consumed_by.objects",
        volume=1 if series.volume is not None else 0,
        geometry=1 if series.geometry is not None else 0,
    )
    ledger.record(
        "collapse.consumed_by.objects",
        background_split=1 if np.isfinite(background_split) else 0,
    )
    measurement = _measure_series(series, request, background_split)
    interiors = measurement.interiors
    ledger.record(
        "objects.produced",
        measured=1 if measurement.code == "measured" else 0,
        interiors=1 if interiors is not None else 0,
        territories=int(interiors.labels.max(initial=0))
        if interiors is not None
        else 0,
        edges=len(interiors.edge_regions) if interiors is not None else 0,
    )
    return measurement


def _measure_series(
    series: Series, request: AnalysisRequest, background_split: float
) -> SeriesMeasurement:
    if series.volume is None:
        return SeriesMeasurement("no_stacked_volume")
    if series.geometry is None:
        return SeriesMeasurement("geometry_unreadable")
    # The ONE rule for which slice a study is read at (task 7.1), shared with the field's
    # structural reading; a request outside the stack is named, never clamped.
    index = selected_slice(len(series.volume), request.slice_index)
    if index is None:
        return SeriesMeasurement(
            "slice_unavailable",
            request.slice_index,
            validation_code="invalid_slice_index",
        )
    geometry = series.geometry
    source = series.slices[index].path.name
    try:
        frame = PlaneFrame.from_dicom(
            geometry.position[index],
            geometry.orientation[index],
            geometry.spacing[index],
        )
    except ValueError as error:
        return SeriesMeasurement(
            "geometry_unreadable",
            index,
            validation_code=str(error),
            source_plane=source,
            orientation_spread=geometry.orientation_spread,
        )
    # The study stage read the thickness once, from the header it owns (task 7.2); this stage
    # consumes that reading rather than opening the header a second time.
    thickness = (
        series.slice_thickness_mm[index]
        if index < len(series.slice_thickness_mm)
        else None
    )
    plane = series.volume[index]
    squint = physical_squint(plane, frame.spacing_rc, request.tile_mm)
    direction = np.asarray(request.direction_lps, dtype=np.float64)
    axes = frame.basis_lps / frame.spacing_rc
    interiors = (
        read_interiors(
            plane,
            frame.spacing_rc,
            background_split,
            request.prominence_mm,
            np.asarray(request.offsets_mm),
            request.backend,
            metric_rc=axes.T @ axes,
        )
        if request.prominence_mm is not None
        else None
    )
    # What bounds each territory, and the relief between those that touch. It reads only values
    # B1 already returned, so it adds no source pass and assigns no anatomy.
    boundaries = (
        boundary_census(
            interiors.labels,
            interiors.distance_mm,
            interiors.edge_regions,
            interiors.edge_kinds,
            request.minimum_divide_sites,
        )
        if interiors is not None
        else None
    )
    # Coefficients in the retained affine basis, not dot products with rounded axes.
    projected = np.linalg.pinv(axes) @ direction
    norm = float(np.linalg.norm(axes @ projected))
    if norm <= np.finfo(np.float64).eps:
        return SeriesMeasurement(
            "axis_unavailable",
            index,
            frame,
            squint,
            None,
            norm,
            handed_on(plane.copy()),
            source_plane=source,
            orientation_spread=geometry.orientation_spread,
            interiors=interiors,
            slice_thickness_mm=thickness,
            boundaries=boundaries,
        )
    bounds = squint.bounds_rc.reshape(-1, 4)
    points = np.column_stack(
        ((bounds[:, 0] + bounds[:, 1] - 1) / 2, (bounds[:, 2] + bounds[:, 3] - 1) / 2)
    )
    normals = np.broadcast_to(projected / norm, points.shape)
    profiles = sample_profiles(
        plane,
        points,
        normals,
        np.asarray(request.offsets_mm),
        frame.spacing_rc,
        request.backend,
        metric_rc=axes.T @ axes,
    )
    return SeriesMeasurement(
        "measured",
        index,
        frame,
        squint,
        profiles,
        norm,
        handed_on(plane.copy()),
        handed_on(points),
        handed_on(normals.copy()),
        source_plane=source,
        orientation_spread=geometry.orientation_spread,
        interiors=interiors,
        slice_thickness_mm=thickness,
        boundaries=boundaries,
    )
