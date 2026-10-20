"""Draw the patella's profile, its pointed planes and what the extensor tendons and the fat pads
read beside them, from saved production records (development only, `run_interiors.py --draw`).

Per fat-suppressed series that read the patella, one picture: the supported marrow-body area
through the stack's physical depth (the pointed planes marked; a slice not read or unreadable is a
gap, never a zero), then the middle slice and every pointed plane at its native pixels with the
parts the established rules named outlined, and the other sequence's slice through each, with the
patella laid on, the tendons read there, and the dark bands its light read. Nothing is decided here:
every outline is read from the saved arrays and the receipt; the planes' own pixels are read from
the series, since a run keeps only the middle slice's.
"""

from collections.abc import Callable
from contextlib import ExitStack
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

from knee.array_archive import open_arrays
from knee.json_store import load_json
from knee.objects.assignments import OBJECT_CODES

PANEL_INCH = 4.5
# One colour for each part drawn, by its object code; the seam of the pads is white.
COLOURS = {
    "patella": "red",
    "hoffa_fat_pad": "orange",
    "suprapatellar_fat": "cyan",
    "patellar_tendon": "lime",
    "quadriceps_tendon": "magenta",
}
MARGIN_PX = 40


def window(plane: np.ndarray) -> np.ndarray:
    """The plane's pixels as grey, the 1st to the 99th percentile of what is finite."""
    values = np.asarray(plane, dtype=float)
    low, high = np.nanpercentile(values[np.isfinite(values)], (1, 99))
    return np.clip((values - low) / max(high - low, 1e-9), 0, 1)


def draw(
    run_dir: Path, study_uid: str, out: Path, volume_of: Callable[[str], np.ndarray]
) -> list[Path]:
    """One picture per fat-suppressed series of the study that read the patella."""
    receipt = load_json(run_dir / "receipt.json")
    records = [r for r in _records(receipt) if r.get("study_uid") == study_uid]
    out.mkdir(parents=True, exist_ok=True)
    drawn: list[Path] = []
    for record in records:
        part = record.get("patella", {})
        if "pointed_planes" not in part:
            continue
        with ExitStack() as stack:
            arrays = stack.enter_context(
                open_arrays(run_dir / record["artifact"], allow_pickle=False)
            )
            prefix = part.get("twin_arrays_prefix")
            twin_record = next(
                (r for r in records if prefix and f"{prefix}_slices" in r["arrays"]),
                None,
            )
            twin = (
                None
                if twin_record is None
                else (
                    twin_record,
                    stack.enter_context(
                        open_arrays(
                            run_dir / twin_record["artifact"], allow_pickle=False
                        )
                    ),
                )
            )
            drawn.append(_picture(record, part, arrays, volume_of, twin, prefix, out))
    return drawn


def _records(node):
    if isinstance(node, dict):
        if "series_uid" in node and "arrays" in node:
            yield node
        for value in node.values():
            yield from _records(value)
    elif isinstance(node, list):
        for value in node:
            yield from _records(value)


def _crop(masks: list[np.ndarray], shape: tuple[int, int]) -> tuple[slice, slice]:
    """The window round the parts drawn: their bounding box and a margin of pixels."""
    held = np.zeros(shape, dtype=bool)
    for mask in masks:
        held |= mask
    if not held.any():
        return slice(0, shape[0]), slice(0, shape[1])
    rows, cols = np.flatnonzero(held.any(axis=1)), np.flatnonzero(held.any(axis=0))
    return (
        slice(max(0, rows[0] - MARGIN_PX), min(shape[0], rows[-1] + MARGIN_PX)),
        slice(max(0, cols[0] - MARGIN_PX), min(shape[1], cols[-1] + MARGIN_PX)),
    )


def _outline(axis, objects: np.ndarray, names, crop) -> None:
    for name in names:
        mask = objects == OBJECT_CODES[name]
        if mask.any():
            axis.contour(
                mask[crop].astype(float), [0.5], colors=COLOURS[name], linewidths=0.9
            )


def _picture(record, part, arrays, volume_of, twin, prefix, out: Path) -> Path:
    planes = part["pointed_planes"]
    uid = record["series_uid"]
    volume = volume_of(uid)
    middle = record["slice_index"]
    shown = [("middle", middle)] + [
        (f"plane {k}", p["slice"]) for k, p in enumerate(planes) if not p["middle"]
    ]
    twins = 0 if twin is None else len(twin[1][f"{prefix}_slices"])
    cols = 1 + len(shown) + twins + (1 if twin is not None else 0)
    figure, axes = plt.subplots(
        1, cols, figsize=(PANEL_INCH * cols, PANEL_INCH), squeeze=False
    )
    axes = list(axes[0])
    area = arrays["a3_patella_profile_area_mm2"]
    position = arrays["a3_patella_depth_offsets_mm"]
    x = position if np.isfinite(position).all() else np.arange(len(area))
    first = axes.pop(0)
    first.plot(x, area, "o-", ms=3, color="tab:blue")
    for slice_ in arrays["a3_patella_pointed_slices"]:
        first.axvline(x[slice_], color="tab:red", lw=0.8)
    first.axvline(x[middle], color="tab:green", lw=0.8, ls=":")
    for z in np.flatnonzero(~np.isfinite(area)):
        first.plot(
            [x[z]], [0], "kx", ms=4
        )  # not read, unreadable or cut: a gap, not zero
    first.set_title(
        f"patella marrow-body area (mm2)\n{record['view']} outcome {part['outcome']}",
        fontsize=8,
    )
    first.set_xlabel("position along the normal (mm); red pointed, green middle")
    stacked = list(arrays["a3_patella_plane_slices"])
    for axis, (label, z) in zip(axes, shown, strict=False):
        pixels = np.asarray(volume[z])
        if z == middle:
            objects, pads, ridge = arrays["a1_objects"], None, None
            pads = [
                arrays.get("a2_quadriceps_fat_pad"),
                arrays.get("a2_prefemoral_fat_pad"),
            ]
            ridge = arrays.get("a2_suprapatellar_recess_ridge")
            code = "bootstrap"
        else:
            row = stacked.index(z)
            objects = arrays["a3_patella_plane_objects"][row]
            pads = [
                arrays["a3_patella_plane_pad_anterior"][row],
                arrays["a3_patella_plane_pad_posterior"][row],
            ]
            ridge = arrays["a3_patella_plane_pad_ridge"][row]
            code = next(p["code"] for p in planes if p["slice"] == z)
        crop = _crop([objects == OBJECT_CODES["patella"]], pixels.shape)
        axis.imshow(window(pixels)[crop], cmap="gray", interpolation="nearest")
        _outline(axis, objects, COLOURS, crop)
        for mask, colour in zip(pads, ("yellow", "blue"), strict=True):
            if mask is not None and mask.any():
                axis.contour(
                    mask[crop].astype(float), [0.5], colors=colour, linewidths=0.7
                )
        if ridge is not None and ridge.any():
            axis.imshow(
                np.ma.masked_equal(ridge[crop], 0),
                cmap="gray_r",
                alpha=0.9,
                vmin=0,
                vmax=1,
            )
        axis.set_title(f"{label}: slice {z}\n{code}", fontsize=8)
        axis.axis("off")
    rest = axes[len(shown) :]
    if twin is not None:
        t_record, t_arrays = twin
        t_volume = volume_of(t_record["series_uid"])
        names = ("patella", "hoffa_fat_pad", "suprapatellar_fat")
        rows = list(range(twins))
        # the middle's twin: the partner slice's own bootstrap naming
        for axis in rest[:1]:
            z = t_record["slice_index"]
            pixels = np.asarray(t_volume[z])
            objects = t_arrays["a1_objects"]
            crop = _crop([objects == OBJECT_CODES["patella"]], pixels.shape)
            axis.imshow(window(pixels)[crop], cmap="gray", interpolation="nearest")
            _outline(axis, objects, COLOURS, crop)
            axis.set_title(f"twin of the middle: slice {z}\nbootstrap", fontsize=8)
            axis.axis("off")
        for axis, k in zip(rest[1:], rows, strict=False):
            z = int(t_arrays[f"{prefix}_slices"][k])
            pixels = np.asarray(t_volume[z])
            objects = t_arrays[f"{prefix}_objects"][k]
            crop = _crop([objects == OBJECT_CODES["patella"]], pixels.shape)
            axis.imshow(window(pixels)[crop], cmap="gray", interpolation="nearest")
            bands = t_arrays[f"{prefix}_bands"][k][crop]
            axis.imshow(
                np.ma.masked_equal(bands, 0),
                cmap="tab10",
                alpha=0.25,
                interpolation="nearest",
            )
            _outline(axis, objects, names, crop)
            for name in ("patellar_tendon", "quadriceps_tendon"):
                mask = t_arrays[f"{prefix}_{name}"][k]
                if mask.any():
                    axis.contour(
                        mask[crop].astype(float),
                        [0.5],
                        colors=COLOURS[name],
                        linewidths=0.9,
                    )
            axis.set_title(
                f"twin slice {z}: patella laid, tendons read\n(tinted: dark bands)",
                fontsize=8,
            )
            axis.axis("off")
    path = out / f"{uid[-8:]}-patella.png"
    figure.savefig(path, dpi=100, bbox_inches="tight")
    plt.close(figure)
    return path
