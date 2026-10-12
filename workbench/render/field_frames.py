"""Draw the field stage's saved values: the squint's four maps and the regime key, one row per series.

Task 6.9 of `openspec/changes/every-stage-renders`, which task 4b.7 declared. `collapse` computes two
things per series, the regime key and the squint, and the writer saves both. This workbench arranges
them through `knee.pictures.collapse.field_panels`. It takes no measurement of its own: every number
on the page is a saved value, every gap is a named silence and never a zero, and the tiles are
placed in native pixels by the bounds the stage saved.

Each series draws one row: the squint's median, minimum, maximum and coverage, then every regime
reading by name. Four silences are kept apart, because each has its own remedy:

- a tile with no finite pixel is drawn in a colour no value can take, and is "not read";
- a regime reading the field did not make says "not read";
- a regime the field could not read at all says so, with the stage's own reason;
- a reading, a regime or a squint the saved run does not carry says "not saved".

A series with no regime or no squint still draws its row, naming what is absent. The grey scale is
Matplotlib's linear display scale over each map's own saved values; coverage has the fixed scale 0 to 1
that the stage defines for it.
"""

import argparse
import json
from collections.abc import Mapping
from dataclasses import fields
from hashlib import sha256
from pathlib import Path
from textwrap import fill

import numpy as np

from knee.collapse.regime import RegimeKey
from knee.pictures import collapse
from workbench.render._out import PROJECT, ArgumentRefusal

#: The regime key's reading names, taken from the stage's own dataclass. A saved record is checked
#: against this vocabulary, so a reading the stage does not own is refused rather than drawn.
REGIME_READINGS: tuple[str, ...] = tuple(field.name for field in fields(RegimeKey))

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
    lines += [f"{name:<27}{show(value)}" for name, value in frame.readings]
    saved = {name for name, _ in frame.readings}
    unsaved = [name for name in REGIME_READINGS if name not in saved]
    if unsaved:
        lines += [
            "",
            fill("not saved by this run's writer: " + ", ".join(unsaved), width=58),
        ]
    return lines


def tile_edges(bounds_rc: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """The tiles' native column edges and row edges, read straight from the saved bounds.

    `bounds_rc` holds r0, r1, c0, c1 for every tile, so the first row of tiles gives the column
    edges and the first column of tiles gives the row edges. Nothing is computed from pixels.
    """
    columns = np.append(bounds_rc[0, :, 2], bounds_rc[0, -1, 3])
    rows = np.append(bounds_rc[:, 0, 0], bounds_rc[-1, 0, 1])
    return columns, rows


def draw_row(axes, record: dict, frame: collapse.FieldPanels) -> None:
    """Arrange one series: the squint's four maps, then the regime key as text."""
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
    else:
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
            mesh = axis.pcolormesh(
                columns_edges, rows_edges, data, cmap=colours, **limits
            )
            axis.set_aspect("equal")
            axis.invert_yaxis()
            axis.tick_params(labelsize=6)
            axis.figure.colorbar(mesh, ax=axis, shrink=0.8)
            axis.set_title(
                (identity if column == 0 else "") + f"{MAP_TITLES[name]}\n{grid}",
                fontsize=8,
            )
    text = axes[4]
    text.set_axis_off()
    text.set_title("the regime key, every reading by name", fontsize=8)
    text.text(
        0.0,
        1.0,
        "\n".join(regime_lines(frame)),
        transform=text.transAxes,
        va="top",
        family="monospace",
        fontsize=6.5,
    )


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
    if collapse.__file__ is None:
        raise RuntimeError("picture_module_source_unavailable:collapse")

    import matplotlib.pyplot as plt

    target.mkdir(parents=True, exist_ok=True)
    gallery, axes = plt.subplots(
        len(records),
        5,
        figsize=(21, 4.6 * len(records)),
        layout="constrained",
        squeeze=False,
    )
    series = []
    for row, (record, (artifact, frame)) in enumerate(
        zip(records, loaded, strict=True)
    ):
        draw_row(axes[row], record, frame)
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
                "squint": None
                if frame.median is None
                else {
                    "arrays": {name: record["arrays"][name] for name in SQUINT_ARRAYS},
                    "tile_shape_rc": list(frame.tile_shape_rc or ()),
                    "tiles": list(frame.median.shape),
                },
                "frame_kind": "study",
            }
        )
    gallery.suptitle(
        "The field's saved squint and regime key, one row per series\n"
        "fuchsia tiles are not read: no finite pixel in the tile",
        fontsize=11,
    )
    gallery.savefig(target / "series.png", dpi=130)
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
        "legend": {"not_read_tile": UNREAD_COLOUR},
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
