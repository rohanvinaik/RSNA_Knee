"""One physical measurement pass over a loaded series; no anatomical assignments."""

from dataclasses import dataclass

import numpy as np

from knee.collapse.contracts import handed_on
from knee.collapse.interiors import InteriorReading, read_interiors
from knee.collapse.physical import PlaneFrame, Squint, physical_squint
from knee.collapse.profiles import ProfileReading, sample_profiles
from knee.study.series import Series


@dataclass(frozen=True, slots=True)
class AnalysisRequest:
    """Explicit settings, never object admission bars.

    None selects floor(n/2) in Chapter 1's spatial stack order. Offsets run along
    the recorded in-plane unit patient vector, not the unprojected requested axis.
    Probe sites are native pixel-centres of all tiles, including remainder tiles.
    """

    tile_mm: float
    offsets_mm: tuple[float, ...]
    direction_lps: tuple[float, float, float]
    backend: str
    slice_index: int | None = None
    prominence_mm: float | None = None
    conversation: bool = False

    def __post_init__(self) -> None:
        if not np.isfinite(self.tile_mm) or self.tile_mm <= 0:
            raise ValueError("invalid_tile_mm")
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


def measure_series(
    series: Series, request: AnalysisRequest, *, background_split: float = float("nan")
) -> SeriesMeasurement:
    if series.volume is None:
        return SeriesMeasurement("no_stacked_volume")
    if series.geometry is None:
        return SeriesMeasurement("geometry_unreadable")
    index = (
        len(series.volume) // 2 if request.slice_index is None else request.slice_index
    )
    if not 0 <= index < len(series.volume):
        return SeriesMeasurement(
            "slice_unavailable", index, validation_code="invalid_slice_index"
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
    try:
        thickness = float(
            series.slices[index].header.get("SliceThickness", float("nan"))
        )
    except (TypeError, ValueError):
        thickness = float("nan")
    thickness = thickness if np.isfinite(thickness) and thickness > 0 else None
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
    )
