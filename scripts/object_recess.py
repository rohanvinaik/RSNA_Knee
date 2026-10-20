"""Draw the recess family's fluid pointer, its pointed planes and what the existing rules read on them,
from saved production records (development only, `run_interiors.py --draw`).

Per series that read the recess, one picture: the fluid pointer's area through the stack's physical
depth (a slice not read or unreadable is a gap, never a zero; the pointed planes are marked), then the
series' bootstrap slice and every pointed plane at its native pixels, in a window round the corridor the
pointer was read in, with the white the fluid level reads faint, the cavity, its lining, the fluid, the
capsule and the retinacula (with the recess each was read beside) outlined apart. Nothing is decided
here: every outline is read from the saved arrays and the receipt; the planes' own pixels are read from
the series, since a run keeps only the middle slice's.
"""

from collections.abc import Callable
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

from knee.array_archive import open_arrays
from knee.json_store import load_json
from knee.objects.assignments import OBJECT_CODES

PANEL_INCH = 3.6
COLUMNS = 6
MARGIN_PX = 20
# One colour for each mask outlined, by the name the recess family keeps it under.
COLOURS = {
    "fluid": "cyan",
    "recess": "red",
    "lining": "yellow",
    "capsule": "orange",
    "medial_recess": "cyan",
    "lateral_recess": "cyan",
    "medial_wall": "magenta",
    "lateral_wall": "lime",
}
# The bootstrap's own masks, by the array and the part's name.
MIDDLE = {
    "recess": "a2_anterior_synovial_recess",
    "lining": "a2_synovium",
    "capsule": "a2_joint_capsule",
}


def window(plane: np.ndarray) -> np.ndarray:
    """The plane's pixels as grey, the 1st to the 99th percentile of what is finite."""
    values = np.asarray(plane, dtype=float)
    low, high = np.nanpercentile(values[np.isfinite(values)], (1, 99))
    return np.clip((values - low) / max(high - low, 1e-9), 0, 1)


def _records(node):
    if isinstance(node, dict):
        if "series_uid" in node and "arrays" in node:
            yield node
        for value in node.values():
            yield from _records(value)
    elif isinstance(node, list):
        for value in node:
            yield from _records(value)


def draw(
    run_dir: Path, study_uid: str, out: Path, volume_of: Callable[[str], np.ndarray]
) -> list[Path]:
    """One picture per series of the study that read the recess family."""
    receipt = load_json(run_dir / "receipt.json")
    out.mkdir(parents=True, exist_ok=True)
    drawn: list[Path] = []
    for record in _records(receipt):
        part = record.get("recess", {})
        if record.get("study_uid") != study_uid or "pointed_planes" not in part:
            continue
        with open_arrays(run_dir / record["artifact"], allow_pickle=False) as arrays:
            drawn.append(_picture(record, part, arrays, volume_of, out))
    return drawn


def _crop(arrays, shape: tuple[int, int]) -> tuple[slice, slice]:
    """The window round the union of the corridor's tiles over the whole stack."""
    tiles = np.asarray(arrays["a3_recess_corridor_tiles"]).any(axis=0)
    bounds = np.asarray(arrays["squint_bounds_rc"])
    if not tiles.any():
        return slice(0, shape[0]), slice(0, shape[1])
    held = bounds[tiles]
    return (
        slice(
            max(0, int(held[:, 0].min()) - MARGIN_PX),
            min(shape[0], int(held[:, 1].max()) + MARGIN_PX),
        ),
        slice(
            max(0, int(held[:, 2].min()) - MARGIN_PX),
            min(shape[1], int(held[:, 3].max()) + MARGIN_PX),
        ),
    )


def _outline(axis, masks: dict[str, np.ndarray], crop) -> None:
    for name, mask in masks.items():
        if name in COLOURS and np.asarray(mask)[crop].any():
            axis.contour(
                np.asarray(mask)[crop].astype(float),
                [0.5],
                colors=COLOURS[name],
                linewidths=0.9,
                linestyles="dashed" if name.endswith("_recess") else "solid",
            )


def _picture(record, part, arrays, volume_of, out: Path) -> Path:
    planes = part["pointed_planes"]
    uid = record["series_uid"]
    volume = volume_of(uid)
    middle = record["slice_index"]
    rows_in = [p for p in planes if not p["middle"]]
    bootstrap = [p for p in planes if p["middle"]]
    shown = [("bootstrap", middle, None)]
    if bootstrap and bootstrap[0]["slice"] != middle:
        shown.append(("bootstrap (retinacula)", bootstrap[0]["slice"], None))
    shown += [(f"plane {k}", p["slice"], k) for k, p in enumerate(rows_in)]
    plane_rows = -(-len(shown) // COLUMNS)
    figure = plt.figure(
        figsize=(PANEL_INCH * COLUMNS, PANEL_INCH * (1 + plane_rows)),
        layout="constrained",
    )
    grid = figure.add_gridspec(1 + plane_rows, COLUMNS)
    position = np.asarray(arrays["a3_recess_depth_offsets_mm"])
    x = position if np.isfinite(position).all() else np.arange(len(position))
    axis = figure.add_subplot(grid[0, :3])
    area = np.asarray(arrays["a3_recess_profile_area_mm2"])
    axis.plot(x, area, "o-", ms=3, color="tab:blue")
    for p in planes:
        axis.axvline(x[p["slice"]], color="tab:red", lw=0.8)
    axis.axvline(x[middle], color="tab:green", lw=0.8, ls=":")
    for z in np.flatnonzero(~np.isfinite(area)):
        axis.plot([x[z]], [0], "kx", ms=4)
    axis.set_title(
        f"fluid-level block area in the {part['kind']} corridor (mm2)\n{record['view']}",
        fontsize=8,
    )
    axis.set_xlabel("position along the normal (mm)", fontsize=7)
    crop = _crop(arrays, np.shape(volume[0]))
    rows_by_slice = {p["slice"]: k for k, p in enumerate(rows_in)}
    for n, (label, z, row) in enumerate(shown):
        axis = figure.add_subplot(grid[1 + n // COLUMNS, n % COLUMNS])
        axis.imshow(
            window(np.asarray(volume[z]))[crop], cmap="gray", interpolation="nearest"
        )
        masks: dict[str, np.ndarray] = {}
        if row is None and z == middle:
            objects = arrays["a1_objects"]
            masks["fluid"] = objects == OBJECT_CODES["joint_fluid"]
            for name, key in MIDDLE.items():
                if key in arrays.files:
                    masks[name] = arrays[key]
            title = f"{label}: slice {z}"
        elif row is None:
            title = f"{label}: slice {z}\nread by the retinacula stage, not here"
        else:
            for name in COLOURS:
                key = f"a3_recess_plane_{name}"
                if key in arrays.files:
                    masks[name] = arrays[key][row]
            said = {
                k: v
                for k, v in planes[[p["slice"] for p in planes].index(z)][
                    "codes"
                ].items()
                if v == "identified"
            }
            title = f"{label}: slice {z} {rows_by_slice[z]}\n{sorted(said)}".replace(
                "'", ""
            )
        _outline(axis, masks, crop)
        axis.set_title(title, fontsize=6)
        axis.axis("off")
    path = out / f"{uid[-8:]}-recess.png"
    figure.savefig(path, dpi=100)
    plt.close(figure)
    return path
