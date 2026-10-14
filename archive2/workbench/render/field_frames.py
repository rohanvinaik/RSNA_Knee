"""Draw the field stage's saved values: the squint, the regime key and the structural reading, one block per series.

Task 6.9 of `openspec/changes/every-stage-renders`, which task 4b.7 declared, and task 7.1's
structural reading. `collapse` computes three things per series: the regime key, the squint, and
(since 7.1) the structural reading of the selected plane. The writer saves all three. This workbench
arranges them through `knee.pictures.collapse`: `field_panels` for the regime key and the squint,
`structure_panels`, `panels` and `over` for the structural reading. It takes no measurement of its
own: every number on the page is a saved value, every gap is a named silence and never a zero, and
the tiles are placed in native pixels by the bounds the stage saved.

Each series draws two rows. The first is the squint's median, minimum, maximum and coverage, then
the regime key by name, the whole-series histogram the key's background split was read from (with
that split marked), and the key's spread ratio beside the Gaussian reference. The second is the
structural reading: its text, the air, the leg closed, the squint inside the leg and its coverage,
the profile along the header's axis, the two basins and the seam, the darkest places and the
largest bright bodies, and the air's own histogram. Four silences are kept apart, because each has
its own remedy:

- a tile with no finite pixel is drawn in a colour no value can take, and is "not read";
- a regime reading the field did not make says "not read";
- a regime the field could not read at all says so, with the stage's own reason;
- a reading, a regime, a squint or a structural reading the saved run does not carry says "not
  saved".

A series with no regime, no squint or no structural reading still draws its rows, naming what is
absent. The grey scale is Matplotlib's linear display scale over each map's own saved values;
coverage has the fixed scale 0 to 1 that the stage defines for it.

The structural reading's tile maps are placed in native pixels by the squint bounds the objects
stage saved, and only when that stage's squint is this reading's grid: the same tile size, the same
number of tiles and the same plane. Where it is not, the maps are drawn on the tile grid and the
text says why; they are never resampled. The two histograms are kept apart: the regime key's is the
whole series', and carries the background split; the structural reading's is the air's own.
"""

import argparse
import json
from collections.abc import Mapping
from dataclasses import dataclass, fields
from hashlib import sha256
from pathlib import Path
from textwrap import fill

import numpy as np

from knee.absence import CODES as ABSENCE_CODES
from knee.collapse.regime import GAUSSIAN_SPREAD_RATIO, RegimeKey
from knee.pictures import collapse
from workbench.render._out import PROJECT, ArgumentRefusal

#: The regime key's reading names, taken from the stage's own dataclass. A saved record is checked
#: against this vocabulary, so a reading the stage does not own is refused rather than drawn.
REGIME_READINGS: tuple[str, ...] = tuple(field.name for field in fields(RegimeKey))

#: The regime readings that are the whole-series histogram: drawn, never listed value by value.
HISTOGRAM_READINGS: tuple[str, ...] = ("histogram_counts", "histogram_edges")

#: The squint's four maps in drawing order, then the bounds that place them in native pixels.
SQUINT_MAPS: tuple[str, ...] = ("median", "minimum", "maximum", "coverage")
SQUINT_ARRAYS: tuple[str, ...] = (*SQUINT_MAPS, "bounds_rc")

#: A tile colour no value can take, so a tile with no finite pixel is never read as a value.
UNREAD_COLOUR = "#c026d3"

MAP_TITLES = {
    "median": "squint median (stored units)",
    "minimum": "squint minimum (stored units)",
    "maximum": "squint maximum (stored units)",
    "coverage": "squint coverage (share of the tile's pixels that are finite)",
}

#: The structural reading's arrays by the short names the writer gives them in
#: `record["structure"]["arrays"]`, each with the dtype it must have and whether it is native scale
#: (the plane's own shape) or one value per tile of the squint.
STRUCTURE_ARRAYS: Mapping[str, tuple[np.dtype, str]] = {
    "air": (np.dtype(np.bool_), "native"),
    "leg": (np.dtype(np.bool_), "native"),
    "inside": (np.dtype(np.bool_), "tiles"),
    "basins": (np.dtype(np.int8), "tiles"),
    "seam": (np.dtype(np.bool_), "tiles"),
    "dark": (np.dtype(np.bool_), "tiles"),
    "bodies": (np.dtype(np.int32), "tiles"),
    "squint_median": (np.dtype(np.float64), "tiles"),
    "squint_coverage": (np.dtype(np.float64), "tiles"),
}
STRUCTURE_REQUIRED: tuple[str, ...] = (
    "air",
    "leg",
    "inside",
    "basins",
    "seam",
    "dark",
    "bodies",
)
STRUCTURE_SQUINT: tuple[str, ...] = ("squint_median", "squint_coverage")

#: What each structural place is drawn in. Red and blue are native-scale masks over the plane; the
#: rest overlay the tile maps. None of them is a colour a stored value is drawn in.
AIR_COLOUR = (1.0, 0.25, 0.25)
OUTSIDE_COLOUR = (0.2, 0.45, 0.95)
BASIN_COLOURS = ("#2563eb", "#f59e0b")
SEAM_COLOUR = "#16a34a"
DARK_COLOUR = "#06b6d4"
BODY_COLOURS = ("#ef4444", "#a855f7", "#eab308", "#14b8a6", "#ec4899", "#84cc16")

#: One block of the picture per series: two rows of this many columns.
COLUMNS = 9
WIDTH_INCHES = 31.0
BLOCK_INCHES = 8.6
DPI = 105

#: Why a series has no whole-series histogram to draw, by the silence it is.
HISTOGRAM_SILENCES: Mapping[str, str] = {
    "regime_not_saved": "no regime key is saved for this series",
    "histogram_not_saved": "this run's writer did not save the whole-series histogram",
    "histogram_not_made": (
        "the field made no histogram: the saved one is empty, never a row of zero counts"
    ),
}

#: What a saved scalar of the regime key says when it is not a value.
SCALAR_SILENCES: Mapping[str, str] = {
    "regime_not_saved": "no regime key is saved for this series",
    "not_saved": "not saved by this run's writer",
    "not_read": "not read: the field did not make this reading",
}


def saved_array(
    arrays: Mapping[str, np.ndarray], descriptors: dict, name: str, ndim: int
) -> np.ndarray:
    """Validate one saved array against the writer's descriptor: dtype, shape and content digest.

    The digest is the writer's own: sha256 over the dtype string, the shape and the bytes.
    """
    if name not in arrays or name not in descriptors:
        raise ValueError(f"missing_saved_array:{name}")
    array = arrays[name]
    descriptor = descriptors[name]
    if array.dtype.str != descriptor["dtype"]:
        raise ValueError(f"saved_array_dtype_mismatch:{name}")
    if array.shape != tuple(descriptor["shape"]):
        raise ValueError(f"saved_array_shape_mismatch:{name}")
    digest = sha256(
        array.dtype.str.encode() + str(array.shape).encode() + array.tobytes()
    ).hexdigest()
    if digest != descriptor["digest"]:
        raise ValueError(f"saved_array_digest_mismatch:{name}")
    if array.ndim != ndim:
        raise ValueError(f"saved_array_representation_invalid:{name}")
    return array


def saved_field(run: Path, record: dict) -> tuple[Path, collapse.FieldPanels]:
    """Reconstitute one series' field values from its saved record, without measuring.

    Total over a series with no regime key or no squint: those are drawn as the silences they are.
    A saved reading name the stage does not own, a squint that is only partly there, or an array
    whose dtype, shape or digest disagrees with its descriptor means the record and this renderer
    disagree, and that is raised rather than drawn.
    """
    saved = record.get("regime")
    if saved is None:
        code, why, readings = None, None, {}
    else:
        code, why, readings = saved["code"], saved["why"], saved["readings"]
        unknown = [name for name in readings if name not in REGIME_READINGS]
        if unknown:
            raise ValueError(f"saved_regime_reading_unknown:{unknown[0]}")
    artifact = run / record["artifact"]
    descriptors = record["arrays"]
    carried = [name in descriptors for name in SQUINT_ARRAYS]
    carried.append("tile_shape_rc" in record)
    if any(carried) and not all(carried):
        raise ValueError("saved_squint_incomplete")
    squint: dict[str, np.ndarray] = {}
    if all(carried):
        with np.load(artifact, allow_pickle=False) as arrays:
            for name in SQUINT_MAPS:
                squint[name] = saved_array(arrays, descriptors, name, 2)
            squint["bounds_rc"] = saved_array(arrays, descriptors, "bounds_rc", 3)
        shape = squint["median"].shape
        if not squint["median"].size:
            raise ValueError("saved_squint_representation_invalid:median")
        for name in SQUINT_MAPS:
            if squint[name].dtype != np.float64 or squint[name].shape != shape:
                raise ValueError(f"saved_squint_representation_invalid:{name}")
        bounds = squint["bounds_rc"]
        if bounds.dtype != np.int64 or bounds.shape != (*shape, 4):
            raise ValueError("saved_squint_representation_invalid:bounds_rc")
        if len(record["tile_shape_rc"]) != 2:
            raise ValueError("saved_squint_representation_invalid:tile_shape_rc")
    return artifact, collapse.field_panels(
        readings,
        squint.get("median"),
        squint.get("minimum"),
        squint.get("maximum"),
        squint.get("coverage"),
        squint.get("bounds_rc"),
        record.get("tile_shape_rc"),
        code,
        why,
    )


def show(value: object) -> str:
    """One saved reading as text. None is 'not read'; nothing is computed, only formatted."""
    if value is None:
        return "not read"
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, float):
        return f"{value:.6g}"
    if isinstance(value, (list, tuple)):
        return "(" + ", ".join(show(item) for item in value) + ")"
    return str(value)


def show_reading(name: str, value: object) -> str:
    """A regime reading as text; the whole-series histogram is named by its length, not listed."""
    if name in HISTOGRAM_READINGS and isinstance(value, list):
        return f"{len(value)} values, drawn beside"
    return show(value)


def regime_lines(frame: collapse.FieldPanels) -> list[str]:
    """The regime panel's text: the stage's standing, then every saved reading by name."""
    if frame.code is None:
        return [
            "field stage (collapse): regime key not saved",
            fill(
                "the writer of this run saved no regime key for this series", width=58
            ),
        ]
    lines = [
        f"field stage (collapse): {frame.code}",
        fill(f"why: {frame.why}", width=58),
        "",
    ]
    if not frame.readings:
        lines.append(fill("no regime readings are saved for this series", width=58))
        return lines
    lines += [
        f"{name:<27}{show_reading(name, value)}" for name, value in frame.readings
    ]
    saved = {name for name, _ in frame.readings}
    unsaved = [name for name in REGIME_READINGS if name not in saved]
    if unsaved:
        lines += [
            "",
            fill("not saved by this run's writer: " + ", ".join(unsaved), width=58),
        ]
    return lines


def regime_histogram(
    frame: collapse.FieldPanels,
) -> tuple[np.ndarray, np.ndarray] | str:
    """The whole-series histogram the key saved as (counts, edges), or the silence that says why not.

    A key the run did not save, a histogram it did not save, and a histogram the field could not
    make are three different silences. A saved histogram whose edges are not one more than its
    counts, or whose numbers are not what a histogram holds, is a record that disagrees with the
    stage, and is raised.
    """
    if frame.code is None:
        return "regime_not_saved"
    saved = dict(frame.readings)
    if any(name not in saved for name in HISTOGRAM_READINGS):
        return "histogram_not_saved"
    counts, edges = saved["histogram_counts"], saved["histogram_edges"]
    if type(counts) is not list or type(edges) is not list:
        raise ValueError("saved_regime_histogram_invalid")
    if not counts and not edges:
        return "histogram_not_made"
    if (
        len(edges) != len(counts) + 1
        or not all(type(count) is int and count >= 0 for count in counts)
        or not all(
            isinstance(edge, (int, float)) and not isinstance(edge, bool)
            for edge in edges
        )
    ):
        raise ValueError("saved_regime_histogram_invalid")
    drawn_edges = np.array(edges, dtype=np.float64)
    if not np.isfinite(drawn_edges).all():
        raise ValueError("saved_regime_histogram_invalid")
    return np.array(counts, dtype=np.int64), drawn_edges


def saved_scalar(frame: collapse.FieldPanels, name: str) -> tuple[str, float | None]:
    """One regime reading as (standing, value): `read` with its value, or the silence it is.

    `regime_not_saved`, `not_saved` (the key does not carry the reading) and `not_read` (the field
    made none, which the writer saves as None) are three silences and never a zero. A saved value
    that is not a finite number is a record that disagrees with the stage, and is raised.
    """
    if frame.code is None:
        return "regime_not_saved", None
    saved = dict(frame.readings)
    if name not in saved:
        return "not_saved", None
    value = saved[name]
    if value is None:
        return "not_read", None
    if (
        isinstance(value, bool)
        or not isinstance(value, (int, float))
        or not np.isfinite(value)
    ):
        raise ValueError(f"saved_regime_reading_not_a_number:{name}")
    return "read", float(value)


@dataclass(frozen=True, slots=True)
class StructureDrawing:
    """One series' saved structural reading as `knee.pictures.collapse` arranges it, and where its tiles go.

    frame: the structural reading's panels, with every value the writer saved. arranged: the four
    collapse panels over the same values, None when the axis is not in the plane or the squint was
    not read (`panels` needs both). bounds_rc: the objects stage's saved native bounds, held only
    when they place this reading's tile grid; None otherwise. placement: `native`, `no_tiles`, or
    `tile_grid:` and the reason the saved bounds do not place the tiles. arrays: the descriptor key
    of every array drawn, by the writer's short name.
    """

    frame: collapse.StructurePanels
    arranged: collapse.CollapsePanels | None
    bounds_rc: np.ndarray | None
    placement: str
    arrays: dict[str, str]


def saved_number(value: object, where: str) -> float:
    """A saved reading as a float. None, which is how the writer saves a reading not made, is NaN."""
    if value is None:
        return float("nan")
    if (
        isinstance(value, bool)
        or not isinstance(value, (int, float))
        or not np.isfinite(value)
    ):
        raise ValueError(f"saved_structure_not_a_number:{where}")
    return float(value)


def saved_list(value: object, where: str, dtype: type) -> np.ndarray:
    """A saved list as a 1-D array of `dtype`. A float list may hold None, as NaN; no other may."""
    if type(value) is not list:
        raise ValueError(f"saved_structure_not_a_list:{where}")
    if dtype is np.float64:
        return np.array([saved_number(item, where) for item in value], dtype=dtype)
    if not all(type(item) is int for item in value):
        raise ValueError(f"saved_structure_not_whole_numbers:{where}")
    return np.array(value, dtype=dtype)


def tile_placement(
    frame: collapse.StructurePanels,
    bounds_rc: np.ndarray | None,
    tile_shape_rc: tuple[int, int] | None,
) -> str:
    """Where the structural reading's tile maps go: `native`, `no_tiles`, or why the tile grid.

    The saved bounds of the objects stage's squint place these tiles only where that squint is
    this reading's grid: the same tile size, the same number of tiles, and a last tile that ends at
    this plane's last row and column. Any difference is named, and the maps are then drawn on the
    tile grid; nothing is resampled and no bound is derived.
    """
    if frame.squint is None or not frame.squint.size:
        return "no_tiles"
    if bounds_rc is None or tile_shape_rc is None:
        return "tile_grid:objects_squint_bounds_not_saved"
    if tuple(tile_shape_rc) != frame.squint_tile_shape_rc:
        return "tile_grid:tile_size_differs_from_the_objects_squint"
    if bounds_rc.shape[:2] != frame.squint.shape:
        return "tile_grid:tile_count_differs_from_the_objects_squint"
    if (int(bounds_rc[-1, -1, 1]), int(bounds_rc[-1, -1, 3])) != frame.air.shape:
        return "tile_grid:objects_squint_covers_another_plane"
    return "native"


def saved_structure(
    run: Path,
    record: dict,
    bounds_rc: np.ndarray | None,
    tile_shape_rc: tuple[int, int] | None,
) -> StructureDrawing | None:
    """Reconstitute one series' saved structural reading and arrange it, without measuring.

    None when the record saved no structural reading: that is drawn as the silence it is. The
    arrays are found through `record["structure"]["arrays"]` and checked against the top-level
    descriptor table by dtype, shape and digest; the codes against the stage's vocabularies; the
    list-valued readings against each other. Anything that disagrees means the record and this
    renderer disagree, and is raised rather than drawn. `bounds_rc` and `tile_shape_rc` are the
    objects stage's saved squint grid, which `tile_placement` compares with this reading's.
    """
    saved = record.get("structure")
    if saved is None:
        return None
    if type(saved) is not dict:
        raise ValueError("saved_structure_not_a_record")
    for key in ("code", "why", "axis", "superior"):
        if type(saved.get(key)) is not str:
            raise ValueError(f"saved_structure_field_invalid:{key}")
    if saved["code"] not in ABSENCE_CODES:
        raise ValueError(f"saved_structure_code_unknown:{saved['code']}")
    names = saved.get("arrays")
    if type(names) is not dict:
        raise ValueError("saved_structure_arrays_missing")
    for short in STRUCTURE_REQUIRED:
        if type(names.get(short)) is not str:
            raise ValueError(f"saved_structure_array_unnamed:{short}")
    tile_shape = saved.get("squint_tile_shape_rc")
    named = [type(names.get(short)) is str for short in STRUCTURE_SQUINT]
    has_squint = tile_shape is not None
    if not all(named) == any(named) == has_squint:
        raise ValueError("saved_structure_squint_incomplete")
    if has_squint and not (
        isinstance(tile_shape, list)
        and len(tile_shape) == 2
        and all(type(size) is int and size >= 1 for size in tile_shape)
    ):
        raise ValueError("saved_structure_squint_tile_shape_invalid")

    descriptors = record["arrays"]
    wanted = [*STRUCTURE_REQUIRED, *(STRUCTURE_SQUINT if has_squint else ())]
    drawn: dict[str, np.ndarray] = {}
    plane = None
    with np.load(run / record["artifact"], allow_pickle=False) as artifact:
        for short in wanted:
            array = saved_array(artifact, descriptors, names[short], 2)
            if array.dtype != STRUCTURE_ARRAYS[short][0]:
                raise ValueError(f"saved_structure_representation_invalid:{short}")
            drawn[short] = array
        if "acquired_plane" in descriptors:
            plane = saved_array(artifact, descriptors, "acquired_plane", 2)
            if plane.dtype.kind not in "iuf":
                raise ValueError("saved_array_representation_invalid:acquired_plane")
    if drawn["air"].shape != drawn["leg"].shape:
        raise ValueError("saved_structure_shape_mismatch:leg")
    tiles = drawn["inside"].shape
    for short in wanted:
        if STRUCTURE_ARRAYS[short][1] == "tiles" and drawn[short].shape != tiles:
            raise ValueError(f"saved_structure_shape_mismatch:{short}")
    if drawn["air"].size:
        if plane is None:
            raise ValueError("saved_structure_plane_missing")
        if plane.shape != drawn["air"].shape:
            raise ValueError("saved_structure_plane_mismatch")

    profile = saved_list(saved.get("profile"), "profile", np.float64)
    profile_tiles = saved_list(saved.get("profile_tiles"), "profile_tiles", np.int64)
    counts = saved_list(saved.get("histogram_counts"), "histogram_counts", np.int64)
    edges = saved_list(saved.get("histogram_edges"), "histogram_edges", np.float64)
    if profile.shape != profile_tiles.shape:
        raise ValueError("saved_structure_profile_tiles_mismatch")
    if (counts < 0).any() or edges.size != (counts.size + 1 if counts.size else 0):
        raise ValueError("saved_structure_histogram_mismatch")
    dip = saved.get("dip")
    if type(dip) is not int or (dip != -1 and not 0 <= dip < profile.size):
        raise ValueError("saved_structure_dip_invalid")
    if dip >= 0 and not np.isfinite(profile[dip]):
        raise ValueError("saved_structure_dip_invalid")
    saved_counts = saved.get("counts")
    if not isinstance(saved_counts, dict) or not all(
        type(name) is str and type(count) is int and count >= 0
        for name, count in saved_counts.items()
    ):
        raise ValueError("saved_structure_counts_invalid")

    squint = (
        collapse.SavedSquint(
            drawn["squint_median"],
            drawn["squint_coverage"],
            (int(tile_shape[0]), int(tile_shape[1])),
        )
        if has_squint and isinstance(tile_shape, list)
        else None
    )
    reading = collapse.SavedStructure(
        code=saved["code"],
        why=saved["why"],
        axis=saved["axis"],
        superior=saved["superior"],
        air_level=saved_number(saved.get("air_level"), "air_level"),
        air=drawn["air"],
        leg=drawn["leg"],
        histogram_counts=counts,
        histogram_edges=edges,
        squint=squint,
        inside=drawn["inside"],
        profile=profile,
        profile_tiles=profile_tiles,
        dip=dip,
        basins=drawn["basins"],
        seam=drawn["seam"],
        dark_level=saved_number(saved.get("dark_level"), "dark_level"),
        dark=drawn["dark"],
        bodies=drawn["bodies"],
        counts=saved_counts,
    )
    frame = collapse.structure_panels(
        plane if plane is not None else np.zeros((0, 0)), reading
    )
    # `panels` needs an image axis and a squint: with the axis through the stack, or unread, or no
    # squint read, the four collapse panels are not made and each panel says why instead.
    arranged = (
        collapse.panels(
            frame.plane, frame.leg, frame.squint, frame.profile, frame.axis, frame.sign
        )
        if frame.axis is not None and frame.squint is not None
        else None
    )
    placement = tile_placement(frame, bounds_rc, tile_shape_rc)
    return StructureDrawing(
        frame=frame,
        arranged=arranged,
        bounds_rc=bounds_rc if placement == "native" else None,
        placement=placement,
        arrays={short: names[short] for short in wanted},
    )


def tile_edges(bounds_rc: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """The tiles' native column edges and row edges, read straight from the saved bounds.

    `bounds_rc` holds r0, r1, c0, c1 for every tile, so the first row of tiles gives the column
    edges and the first column of tiles gives the row edges. Nothing is computed from pixels.
    """
    columns = np.append(bounds_rc[0, :, 2], bounds_rc[0, -1, 3])
    rows = np.append(bounds_rc[:, 0, 0], bounds_rc[-1, 0, 1])
    return columns, rows


def number(value: float) -> str:
    """A saved level as text: NaN is how a reading not made comes back from the record."""
    return "not read" if np.isnan(value) else f"{value:.6g}"


def structure_lines(drawing: StructureDrawing) -> list[str]:
    """The structural panel's text: the stage's standing, the header codes, the levels and every count."""
    frame = drawing.frame
    dip = (
        "no finite step"
        if frame.dip == -1
        else f"step {frame.dip} (tile {int(frame.profile_tiles[frame.dip])})"
    )
    placement = {
        "native": "in native pixels, by the objects stage's saved squint bounds",
        "no_tiles": "none: no squint was read",
    }.get(
        drawing.placement,
        "on the tile grid: " + drawing.placement.removeprefix("tile_grid:"),
    )
    return [
        f"structure (collapse): {frame.code}",
        fill(f"why: {frame.why}", width=44),
        "",
        "the header's axis, as the field read it",
        f"  axis      {frame.axis_code}",
        f"  superior  {frame.superior_code}",
        "",
        f"air level    {number(frame.air_level)}",
        f"dark level   {number(frame.dark_level)}",
        f"profile dip  {dip}",
        "",
        "counts",
        *(f"  {name:<14}{count}" for name, count in frame.counts.items()),
        "",
        fill(f"tile maps placed {placement}", width=44),
    ]


def silence(axis, title: str, message: str) -> None:
    """An axis that holds a named silence in words, so it can never be read as an empty picture."""
    axis.set_axis_off()
    axis.set_title(title, fontsize=8)
    axis.text(
        0.03,
        0.95,
        fill(message, width=40),
        transform=axis.transAxes,
        va="top",
        fontsize=7,
    )


def native_extent(shape: tuple[int, ...]) -> tuple[float, float, float, float]:
    """An image's extent so its pixel edges fall on whole native coordinates, row 0 at the top."""
    return 0.0, float(shape[1]), float(shape[0]), 0.0


def show_native(axis, rgb: np.ndarray) -> None:
    """A native-scale picture, in native pixel coordinates."""
    axis.imshow(rgb, extent=native_extent(rgb.shape), interpolation="nearest")
    axis.tick_params(labelsize=6)


def tile_axis(axis, drawing: StructureDrawing, recorded: np.ndarray | None):
    """Set an axis up for a tile map and return its (column edges, row edges).

    In native placement the plane is drawn faintly beneath, so the tiles can be read against it;
    otherwise the axis is the tile grid itself. Either way row 0 is at the top.
    """
    if drawing.bounds_rc is not None:
        rows, columns = drawing.frame.air.shape
        if recorded is not None:
            axis.imshow(
                collapse.over(
                    recorded, np.zeros(recorded.shape, dtype=bool), (0.0, 0.0, 0.0)
                ),
                extent=native_extent((rows, columns)),
                interpolation="nearest",
                alpha=0.5,
            )
        edges = tile_edges(drawing.bounds_rc)
    else:
        rows, columns = drawing.frame.inside.shape
        edges = (np.arange(columns + 1), np.arange(rows + 1))
    axis.set_xlim(0, columns)
    axis.set_ylim(rows, 0)
    axis.set_aspect("equal")
    axis.tick_params(labelsize=6)
    return edges


def overlay(axis, edges, mask: np.ndarray, colour: str, alpha: float = 0.65) -> None:
    """Colour the tiles of a boolean tile map, leaving every other tile as it was."""
    from matplotlib.colors import ListedColormap

    columns, rows = edges
    axis.pcolormesh(
        columns,
        rows,
        np.ma.masked_where(~mask, np.ones(mask.shape)),
        cmap=ListedColormap([colour]),
        vmin=0.0,
        vmax=1.0,
        alpha=alpha,
    )


def draw_squint_maps(axes, record: dict, frame: collapse.FieldPanels) -> None:
    """The squint's four maps, each placed in native pixels by the bounds the stage saved."""
    from matplotlib import colormaps

    view, fluid, fat = record["view"]
    identity = (
        f"{fill(record['series_uid'], width=42)}\n"
        f"{view} · fluid-sensitive={fluid}, fat-suppressed={fat}\n"
    )
    if (
        frame.median is None
        or frame.minimum is None
        or frame.maximum is None
        or frame.coverage is None
        or frame.bounds_rc is None
        or frame.tile_shape_rc is None
    ):
        for column, name in enumerate(SQUINT_MAPS):
            axes[column].set_title(
                (identity if column == 0 else "") + MAP_TITLES[name], fontsize=8
            )
            axes[column].text(
                0.03,
                0.95,
                f"no squint saved for this series\n\nobjects stage code: {record['code']}",
                transform=axes[column].transAxes,
                va="top",
            )
            axes[column].set_axis_off()
        return
    tiles_down, tiles_across = frame.median.shape
    tile_rows, tile_columns = frame.tile_shape_rc
    grid = f"{tiles_down}×{tiles_across} tiles of at most {tile_rows}×{tile_columns} px"
    columns_edges, rows_edges = tile_edges(frame.bounds_rc)
    maps = (
        ("median", frame.median),
        ("minimum", frame.minimum),
        ("maximum", frame.maximum),
        ("coverage", frame.coverage),
    )
    for column, (name, data) in enumerate(maps):
        colours = colormaps["viridis" if name == "coverage" else "gray"].copy()
        colours.set_bad(UNREAD_COLOUR)
        limits = {"vmin": 0.0, "vmax": 1.0} if name == "coverage" else {}
        axis = axes[column]
        mesh = axis.pcolormesh(columns_edges, rows_edges, data, cmap=colours, **limits)
        axis.set_aspect("equal")
        axis.invert_yaxis()
        axis.tick_params(labelsize=6)
        axis.figure.colorbar(mesh, ax=axis, shrink=0.8)
        axis.set_title(
            (identity if column == 0 else "") + f"{MAP_TITLES[name]}\n{grid}",
            fontsize=8,
        )


def draw_regime_text(axis, frame: collapse.FieldPanels) -> None:
    """The regime key, every saved reading by name."""
    axis.set_axis_off()
    axis.set_title("the regime key, every reading by name", fontsize=8)
    axis.text(
        0.0,
        1.0,
        "\n".join(regime_lines(frame)),
        transform=axis.transAxes,
        va="top",
        family="monospace",
        fontsize=6.5,
    )


def draw_regime_histogram(
    axis,
    histogram: tuple[np.ndarray, np.ndarray] | str,
    split: tuple[str, float | None],
) -> str:
    """The whole-series histogram, with the background split the field read from it marked.

    The split is the valley of THIS histogram, so it is marked here and on no other. Returns
    `drawn`, or the silence the panel holds.
    """
    if isinstance(histogram, str):
        silence(axis, "the whole series' histogram", HISTOGRAM_SILENCES[histogram])
        return histogram
    counts, edges = histogram
    standing, value = split
    axis.stairs(counts, edges, fill=True, color="#64748b")
    axis.set_yscale("log", nonpositive="clip")
    axis.tick_params(labelsize=6)
    axis.set_xlabel("stored values", fontsize=7)
    note = "the red line is the background split, the valley the field read"
    if value is not None:
        axis.axvline(value, color="#dc2626", linewidth=1.6)
        axis.text(
            value,
            0.98,
            f" background_split {value:.6g}",
            transform=axis.get_xaxis_transform(),
            color="#dc2626",
            fontsize=7,
            va="top",
            ha="left",
        )
    else:
        note = f"background_split: {SCALAR_SILENCES[standing]}"
    axis.set_title(f"the whole series' histogram (log counts)\n{note}", fontsize=8)
    return "drawn"


def draw_spread(axis, spread: tuple[str, float | None]) -> str:
    """The saved spread ratio beside the Gaussian reference, each as its own number.

    No difference between them is computed and no verdict is drawn: the reader compares. Returns
    `drawn`, or the silence the panel holds; the reference is drawn either way.
    """
    standing, value = spread
    top = max(GAUSSIAN_SPREAD_RATIO, value or 0.0) * 1.3
    axis.set_xlim(0.0, top)
    axis.set_ylim(0.0, 1.0)
    axis.set_yticks([])
    axis.tick_params(labelsize=6)
    axis.axvline(GAUSSIAN_SPREAD_RATIO, color="#111827", linestyle="--", linewidth=1.2)
    axis.text(
        GAUSSIAN_SPREAD_RATIO,
        0.97,
        f"Gaussian {GAUSSIAN_SPREAD_RATIO:g} ",
        va="top",
        ha="right",
        fontsize=7,
    )
    axis.set_xlabel("(p95 - p5) / (p75 - p25)", fontsize=7)
    axis.set_title("spread_ratio beside the Gaussian reference", fontsize=8)
    if value is None:
        axis.text(
            0.5,
            0.4,
            fill(f"spread_ratio {SCALAR_SILENCES[standing]}", width=26),
            transform=axis.transAxes,
            ha="center",
            va="center",
            fontsize=7,
        )
        return standing
    axis.barh([0.45], [value], height=0.18, color="#f59e0b")
    axis.text(value, 0.45, f" {value:.6g}", va="center", fontsize=8)
    return "drawn"


def draw_air(axis, drawing: StructureDrawing, recorded: np.ndarray) -> str:
    """The plane with the air in red: the low places that connect to the frame's border."""
    frame = drawing.frame
    show_native(axis, collapse.over(recorded, frame.air, AIR_COLOUR))
    axis.set_title(
        f"the air (red): connected to the border\nair level {number(frame.air_level)}",
        fontsize=8,
    )
    return "drawn"


def draw_leg(axis, drawing: StructureDrawing, recorded: np.ndarray, leg) -> str:
    """The plane with every place outside the closed leg in blue, so the leg is what stays grey."""
    show_native(axis, collapse.over(recorded, ~leg, OUTSIDE_COLOUR))
    axis.set_title(
        f"the leg, closed (grey); outside it blue\nleg places {drawing.frame.counts.get('leg_places', 'not saved')}",
        fontsize=8,
    )
    return "drawn"


def draw_squint(axis, drawing: StructureDrawing, squint: np.ndarray | None) -> str:
    """The squint inside the leg: tile medians, the inside tiles in grey and the partly covered ones apart.

    A tile with no place in the leg has no median and is dark, which is not "not read": the stage
    read it, and nothing of it is leg. A tile with a median that the stage did not count as inside
    is a partly covered edge tile; it is drawn in another scale so it is never taken for an inside
    one.
    """
    from matplotlib import colormaps

    frame = drawing.frame
    if squint is None:
        silence(
            axis,
            "the squint inside the leg",
            f"no squint was read. The stage says: {frame.why}",
        )
        return "not_read"
    edges = tile_axis(axis, drawing, None)
    finite = np.isfinite(squint)
    limits = (
        {"vmin": float(squint[finite].min()), "vmax": float(squint[finite].max())}
        if finite.any()
        else {}
    )
    grey = colormaps["gray"].copy()
    grey.set_bad("#1f2937")
    partial = colormaps["cividis"].copy()
    partial.set_bad(alpha=0.0)
    mesh = axis.pcolormesh(
        *edges, np.where(frame.inside, squint, np.nan), cmap=grey, **limits
    )
    axis.pcolormesh(
        *edges, np.where(finite & ~frame.inside, squint, np.nan), cmap=partial, **limits
    )
    axis.figure.colorbar(mesh, ax=axis, shrink=0.7)
    axis.set_title(
        "the squint inside the leg: tile medians\n"
        "grey inside · blue-yellow partly covered · dark no leg place",
        fontsize=8,
    )
    return "drawn"


def draw_coverage(axis, drawing: StructureDrawing) -> str:
    """The share of each tile that is leg, 0 to 1."""
    frame = drawing.frame
    if frame.squint_coverage is None:
        silence(
            axis,
            "the squint's coverage by the leg",
            f"no squint was read. The stage says: {frame.why}",
        )
        return "not_read"
    edges = tile_axis(axis, drawing, None)
    mesh = axis.pcolormesh(
        *edges, frame.squint_coverage, cmap="viridis", vmin=0.0, vmax=1.0
    )
    axis.figure.colorbar(mesh, ax=axis, shrink=0.7)
    axis.set_title("share of each tile that is leg (0 to 1)", fontsize=8)
    return "drawn"


def draw_profile(axis, drawing: StructureDrawing, profile: np.ndarray) -> str:
    """The profile along the header's axis, superior first, with its dip marked.

    Drawn only where the field read one: with the axis through the stack, unread or ambiguous, or
    no squint, the profile is empty and the panel says so with the stage's own reason.
    """
    frame = drawing.frame
    if not profile.size:
        silence(
            axis,
            "the profile along the header's axis",
            f"no profile was read. The stage says: {frame.why}",
        )
        return "not_read"
    steps = np.arange(profile.size)
    axis.plot(profile, steps, color="black", linewidth=1.2, marker=".", markersize=3)
    axis.set_ylim(profile.size - 0.5, -0.5)
    axis.tick_params(labelsize=6)
    axis.set_xlabel("median of the central third of the inside squint", fontsize=7)
    axis.set_ylabel("step along the axis, superior first", fontsize=7)
    if frame.dip >= 0:
        axis.axhline(frame.dip, color="#dc2626", linewidth=1.6)
        axis.text(
            0.98,
            frame.dip,
            f"dip: step {frame.dip}, tile {int(frame.profile_tiles[frame.dip])}",
            transform=axis.get_yaxis_transform(),
            color="#dc2626",
            fontsize=7,
            ha="right",
            va="bottom",
            bbox={"facecolor": "white", "edgecolor": "none", "alpha": 0.8, "pad": 1},
        )
    arranged = drawing.arranged
    where = (
        f"image axis {arranged.axis}, sign {arranged.sign:+.0f}"
        if arranged is not None
        else f"axis {frame.axis_code}"
    )
    axis.set_title(
        "the profile along the header's axis\n"
        + (where if frame.dip >= 0 else f"{where} · no finite step"),
        fontsize=8,
    )
    return "drawn"


def draw_basins(axis, drawing: StructureDrawing, recorded: np.ndarray) -> str:
    """The two basins and the seam between them, over the plane; or the stage's reason there are none."""
    frame = drawing.frame
    if frame.inside.size == 0:
        silence(
            axis,
            "the two basins and the seam",
            f"no squint was read. The stage says: {frame.why}",
        )
        return "not_read"
    if not frame.basins.any():
        silence(
            axis,
            "the two basins and the seam",
            f"no tile carries a basin label. The stage says: {frame.why}",
        )
        return "not_read"
    edges = tile_axis(axis, drawing, recorded)
    for label, colour in enumerate(BASIN_COLOURS, start=1):
        overlay(axis, edges, frame.basins == label, colour)
    overlay(axis, edges, frame.seam, SEAM_COLOUR, alpha=0.95)
    axis.set_title(
        "the two basins (blue 1, amber 2)\nand the seam between them (green)",
        fontsize=8,
    )
    return "drawn"


def draw_dark_and_bodies(axis, drawing: StructureDrawing, recorded: np.ndarray) -> str:
    """The darkest places inside the leg and the ranked bright bodies, over the plane."""
    frame = drawing.frame
    if frame.inside.size == 0:
        silence(
            axis,
            "the darkest places and the largest bright bodies",
            f"no squint was read. The stage says: {frame.why}",
        )
        return "not_read"
    edges = tile_axis(axis, drawing, recorded)
    for rank in (int(value) for value in np.unique(frame.bodies) if value > 0):
        overlay(
            axis,
            edges,
            frame.bodies == rank,
            BODY_COLOURS[(rank - 1) % len(BODY_COLOURS)],
        )
    overlay(axis, edges, frame.dark, DARK_COLOUR, alpha=0.8)
    axis.set_title(
        f"the darkest places (cyan, at or below {number(frame.dark_level)})\n"
        f"and the largest bright bodies by rank ({frame.counts.get('bodies_total', 'not saved')} in all)",
        fontsize=8,
    )
    return "drawn"


def draw_air_histogram(axis, drawing: StructureDrawing) -> str:
    """The air's own values. This is the structural reading's histogram, not the regime key's."""
    frame = drawing.frame
    counts, edges = frame.histogram
    if not counts.size:
        silence(
            axis,
            "the air's own values",
            f"no air histogram: the field found no air. The stage says: {frame.why}",
        )
        return "not_read"
    axis.stairs(counts, edges, fill=True, color="#dc2626")
    axis.set_yscale("log", nonpositive="clip")
    axis.tick_params(labelsize=6)
    axis.set_xlabel("stored values", fontsize=7)
    if np.isfinite(frame.air_level):
        axis.axvline(frame.air_level, color="black", linestyle="--", linewidth=1.2)
    axis.set_title(
        "the air's own values (log counts)\n"
        f"dashed: the level the air was read at, {number(frame.air_level)}",
        fontsize=8,
    )
    return "drawn"


def draw_structure_row(
    figure, grid, row: int, drawing: StructureDrawing | None
) -> dict:
    """The structural reading's row of a series' block, and the status of each of its panels.

    A series that saved no structural reading draws one axis that says so. A reading in which no
    plane was read says so across the row, with the stage's own reason. Otherwise every panel is
    drawn, each answering for itself: one the stage did not read says why and the rest still draw.
    """
    if drawing is None:
        silence(
            figure.add_subplot(grid[row, :]),
            "the field's structural reading",
            "no structural reading is saved for this series: this run's writer saved none",
        )
        return {"structure": "not_saved"}
    frame = drawing.frame
    text = figure.add_subplot(grid[row, 0])
    text.set_axis_off()
    text.set_title("the field's structural reading", fontsize=8)
    text.text(
        0.0,
        1.0,
        "\n".join(structure_lines(drawing)),
        transform=text.transAxes,
        va="top",
        family="monospace",
        fontsize=6.5,
    )
    if frame.air.size == 0:
        silence(
            figure.add_subplot(grid[row, 1:]),
            "the structural panels",
            "no plane was read, so no air, leg, squint, profile, basins, seam, darkest places or "
            f"bodies are drawn. The stage says: {frame.why}",
        )
        return {"structure": "no_plane_read"}
    arranged = drawing.arranged
    recorded = arranged.recorded if arranged is not None else frame.plane
    leg = arranged.leg if arranged is not None else frame.leg
    squint = arranged.squint if arranged is not None else frame.squint
    profile = arranged.profile if arranged is not None else frame.profile
    return {
        "air": draw_air(figure.add_subplot(grid[row, 1]), drawing, recorded),
        "leg": draw_leg(figure.add_subplot(grid[row, 2]), drawing, recorded, leg),
        "squint": draw_squint(figure.add_subplot(grid[row, 3]), drawing, squint),
        "coverage": draw_coverage(figure.add_subplot(grid[row, 4]), drawing),
        "profile": draw_profile(figure.add_subplot(grid[row, 5]), drawing, profile),
        "basins_and_seam": draw_basins(
            figure.add_subplot(grid[row, 6]), drawing, recorded
        ),
        "dark_and_bodies": draw_dark_and_bodies(
            figure.add_subplot(grid[row, 7]), drawing, recorded
        ),
        "air_histogram": draw_air_histogram(figure.add_subplot(grid[row, 8]), drawing),
    }


def structure_manifest(
    record: dict, drawing: StructureDrawing | None, panels: dict
) -> dict | None:
    """What was drawn of the structural reading, from the saved values: the codes, the arrays, each panel's status."""
    if drawing is None:
        return None
    frame = drawing.frame
    return {
        "code": frame.code,
        "why": frame.why,
        "axis_code": frame.axis_code,
        "superior_code": frame.superior_code,
        "placement": drawing.placement,
        "counts": dict(frame.counts),
        "arrays": {
            short: record["arrays"][key] for short, key in drawing.arrays.items()
        },
        "panels": panels,
    }


def draw(run: Path, study_uid: str, out: Path) -> dict:
    """Draw this stage from the saved run and return its manifest.

    The one entry a caller uses, so the single command can draw every stage without knowing each
    renderer's argument spelling. `main()` is a thin wrapper over it, so the hand-typed command
    and the joined run draw the same thing from the same code.

    Matplotlib is supplied PER RUN and is never a production dependency, so it is imported after
    every refusal this function can make: the validators above are then importable and testable in
    the ordinary environment.
    """
    target = out.resolve()
    if not target.is_relative_to((PROJECT / "data").resolve()):
        raise ArgumentRefusal("out must be under the project's private data directory")
    receipt_path = run / "receipt.json"
    receipt_bytes = receipt_path.read_bytes()
    receipt = json.loads(receipt_bytes)
    records = [r for r in receipt["records"] if r["study_uid"] == study_uid]
    if not records:
        raise ArgumentRefusal("no saved records for this study")
    loaded = [saved_field(run, record) for record in records]
    structures = [
        saved_structure(run, record, frame.bounds_rc, frame.tile_shape_rc)
        for record, (_, frame) in zip(records, loaded, strict=True)
    ]
    histograms = [regime_histogram(frame) for _, frame in loaded]
    splits = [saved_scalar(frame, "background_split") for _, frame in loaded]
    spreads = [saved_scalar(frame, "spread_ratio") for _, frame in loaded]
    if collapse.__file__ is None:
        raise RuntimeError("picture_module_source_unavailable:collapse")

    import matplotlib.pyplot as plt

    target.mkdir(parents=True, exist_ok=True)
    gallery = plt.figure(
        figsize=(WIDTH_INCHES, BLOCK_INCHES * len(records)), layout="constrained"
    )
    grid = gallery.add_gridspec(2 * len(records), COLUMNS)
    series = []
    for block, (record, (artifact, frame)) in enumerate(
        zip(records, loaded, strict=True)
    ):
        regime_row = 2 * block
        draw_squint_maps(
            [gallery.add_subplot(grid[regime_row, column]) for column in range(4)],
            record,
            frame,
        )
        draw_regime_text(gallery.add_subplot(grid[regime_row, 4:6]), frame)
        histogram_status = draw_regime_histogram(
            gallery.add_subplot(grid[regime_row, 6:8]), histograms[block], splits[block]
        )
        spread_status = draw_spread(
            gallery.add_subplot(grid[regime_row, 8]), spreads[block]
        )
        panels = draw_structure_row(gallery, grid, regime_row + 1, structures[block])
        series.append(
            {
                "series_uid": record["series_uid"],
                "artifact": record["artifact"],
                "artifact_sha256": sha256(artifact.read_bytes()).hexdigest(),
                "view": record["view"],
                "objects_stage_code": record["code"],
                "regime": {
                    "code": frame.code,
                    "why": frame.why,
                    "readings": dict(frame.readings),
                },
                "regime_histogram": histogram_status,
                "background_split": {
                    "standing": splits[block][0],
                    "value": splits[block][1],
                },
                "spread_ratio": {
                    "standing": spreads[block][0],
                    "value": spreads[block][1],
                    "gaussian_reference": GAUSSIAN_SPREAD_RATIO,
                    "panel": spread_status,
                },
                "squint": None
                if frame.median is None
                else {
                    "arrays": {name: record["arrays"][name] for name in SQUINT_ARRAYS},
                    "tile_shape_rc": list(frame.tile_shape_rc or ()),
                    "tiles": list(frame.median.shape),
                },
                "structure": structure_manifest(record, structures[block], panels),
                "frame_kind": "study",
            }
        )
    gallery.suptitle(
        "The field's saved squint, regime key and structural reading, one block per series\n"
        "fuchsia tiles are not read: no finite pixel in the tile",
        fontsize=11,
    )
    gallery.savefig(target / "series.png", dpi=DPI)
    plt.close(gallery)
    manifest = {
        "schema": "field-frames-v1",
        "receipt_sha256": sha256(receipt_bytes).hexdigest(),
        "renderer_sha256": sha256(Path(__file__).read_bytes()).hexdigest(),
        "picture_module_sha256": {
            "collapse": sha256(Path(collapse.__file__).read_bytes()).hexdigest()
        },
        "study_uid": study_uid,
        "image": "series.png",
        "frame_kind": "study",
        "legend": {
            "not_read_tile": UNREAD_COLOUR,
            "air": list(AIR_COLOUR),
            "outside_the_leg": list(OUTSIDE_COLOUR),
            "basin_1": BASIN_COLOURS[0],
            "basin_2": BASIN_COLOURS[1],
            "seam": SEAM_COLOUR,
            "darkest_places": DARK_COLOUR,
            "bodies_by_rank": list(BODY_COLOURS),
        },
        "series": series,
        "note": (
            "Every value is a saved one. 'not read' is a tile or a reading the field did not "
            "make; 'not saved' is something this run's writer did not carry; neither is a zero."
        ),
    }
    (target / "manifest.json").write_text(
        json.dumps(manifest, indent=2, allow_nan=False) + "\n"
    )
    return manifest


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("run", type=Path)
    parser.add_argument("--study-uid", required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    # ONLY the argument refusals. A saved-array digest mismatch or a malformed receipt is a
    # corruption signal and must propagate, never be dressed as a mistyped flag.
    try:
        draw(args.run, args.study_uid, args.out)
    except ArgumentRefusal as refusal:
        parser.error(str(refusal))
    target = args.out.resolve()
    print(
        json.dumps(
            {
                "series": str(target / "series.png"),
                "manifest": str(target / "manifest.json"),
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
