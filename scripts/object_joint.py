"""Draw the joint's profiles, its pointed planes and what the existing rules read on them, from saved
production records (development only, `run_interiors.py --draw`).

Per series that read the joint, one picture: the four quantities' areas through the stack's physical
depth, each on its own axis (a slice not read or unreadable is a gap, never a zero; the pointed planes
are marked), then the middle slice and every pointed plane at its native pixels, in a window round the
joint's corridor, with the parts the existing rules named outlined and the candidates the rules' gates
refuse (the sagittal horns, the sagittal cartilage) drawn apart. Nothing is decided here: every
outline is read from the saved arrays and the receipt; the planes' own pixels are read from the
series, since a run keeps only the middle slice's.
"""

import json
from collections.abc import Callable
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

from knee.objects.assignments import OBJECT_CODES

PANEL_INCH = 3.6
COLUMNS = 6
# One colour for each part outlined, by its object code.
COLOURS = {
    "medial_meniscus": "dodgerblue",
    "lateral_meniscus": "cyan",
    "meniscus": "white",
    "femoral_cartilage": "yellow",
    "tibial_cartilage": "orange",
    "mcl": "magenta",
    "pcl": "lime",
    "acl": "red",
    "femur": "#555555",
    "tibia": "#555555",
}
QUANTITIES = ("dark", "ligament", "bright", "fluid")
MARGIN_PX = 20


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
    """One picture per series of the study that read the joint."""
    receipt = json.loads((run_dir / "receipt.json").read_text())
    out.mkdir(parents=True, exist_ok=True)
    drawn: list[Path] = []
    for record in _records(receipt):
        part = record.get("joint", {})
        if record.get("study_uid") != study_uid or "pointed_planes" not in part:
            continue
        arrays = np.load(run_dir / record["artifact"])
        drawn.append(_picture(record, part, arrays, volume_of, out))
    return drawn


def _crop(arrays, shape: tuple[int, int]) -> tuple[slice, slice]:
    """The window round the union of the corridor's tiles over the whole stack."""
    tiles = np.asarray(arrays["a3_joint_corridor_tiles"]).any(axis=0)
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


def _outline(axis, objects: np.ndarray, crop) -> None:
    for name, colour in COLOURS.items():
        mask = objects == OBJECT_CODES[name]
        if mask[crop].any():
            axis.contour(
                mask[crop].astype(float),
                [0.5],
                colors=colour,
                linewidths=0.5 if name in ("femur", "tibia") else 0.9,
            )


def _picture(record, part, arrays, volume_of, out: Path) -> Path:
    planes = part["pointed_planes"]
    uid = record["series_uid"]
    volume = volume_of(uid)
    middle = record["slice_index"]
    names = [q for q in QUANTITIES if f"a3_joint_{q}_area_mm2" in arrays.files]
    rows_in = [p for p in planes if not p["middle"]]
    shown = [("middle", middle, None)] + [
        (f"plane {k}", p["slice"], k) for k, p in enumerate(rows_in)
    ]
    plane_rows = -(-len(shown) // COLUMNS)
    figure = plt.figure(
        figsize=(PANEL_INCH * COLUMNS, PANEL_INCH * (1 + plane_rows)),
        layout="constrained",
    )
    grid = figure.add_gridspec(1 + plane_rows, COLUMNS)
    position = np.asarray(arrays["a3_joint_depth_offsets_mm"])
    depth = len(position)
    x = position if np.isfinite(position).all() else np.arange(depth)
    pointed = {p["slice"]: p["pointed_by"] for p in planes}
    for k, q in enumerate(names):
        axis = figure.add_subplot(grid[0, k])
        area = np.asarray(arrays[f"a3_joint_{q}_area_mm2"])
        axis.plot(x, area, "o-", ms=3, color="tab:blue")
        for z, by in pointed.items():
            if q in by:
                axis.axvline(x[z], color="tab:red", lw=0.8)
        axis.axvline(x[middle], color="tab:green", lw=0.8, ls=":")
        for z in np.flatnonzero(~np.isfinite(area)):
            axis.plot([x[z]], [0], "kx", ms=4)
        axis.set_title(f"{q} area (mm2)\n{record['view']}", fontsize=8)
        axis.set_xlabel("position along the normal (mm)", fontsize=7)
    crop = _crop(arrays, np.shape(volume[0]))
    for n, (label, z, row) in enumerate(shown):
        axis = figure.add_subplot(grid[1 + n // COLUMNS, n % COLUMNS])
        pixels = np.asarray(volume[z])
        axis.imshow(window(pixels)[crop], cmap="gray", interpolation="nearest")
        if row is None:
            objects = arrays["a1_objects"]
            title = f"{label}: slice {z}\nbootstrap"
        else:
            objects = arrays["a3_joint_plane_objects"][row]
            reading = arrays["a3_joint_plane_reading"][row]
            ends = arrays["a3_joint_plane_horn_end"][row]
            for value, colour in ((1, "lime"), (2, "magenta")):
                if (ends[crop] == value).any():
                    axis.contour(
                        (ends[crop] == value).astype(float),
                        [0.5],
                        colors=colour,
                        linewidths=0.9,
                        linestyles="dashed",
                    )
            for name in ("femoral_cartilage", "tibial_cartilage"):
                mask = reading == OBJECT_CODES[name]
                if mask[crop].any():
                    axis.contour(
                        mask[crop].astype(float),
                        [0.5],
                        colors=COLOURS[name],
                        linewidths=0.6,
                        linestyles="dashed",
                    )
            codes = planes[[p["slice"] for p in planes].index(z)]
            keep = {
                k: v
                for k, v in codes["codes"].items()
                if v == "identified" or k in ("horns", "cartilage_reading")
            }
            comp = codes["compartment"]
            title = f"{label}: slice {z} {pointed[z]}\n{comp or ''} {sorted(keep.items())}".replace(
                "'", ""
            )
        _outline(axis, objects, crop)
        axis.set_title(title, fontsize=6)
        axis.axis("off")
    path = out / f"{uid[-8:]}-joint.png"
    figure.savefig(path, dpi=100)
    plt.close(figure)
    return path
