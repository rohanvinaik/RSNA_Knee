"""Draw the femur's and the tibia's profile and pointed planes from saved production records
(development only, `run_interiors.py --draw`).

Per series that profiled a bone, one picture per bone: the supported marrow-body area through the
stack's physical depth (the pointed planes marked; a slice not read or unreadable is a gap, never a
zero), then every pointed plane at its native pixels with the territory the carried places named
(orange) outlined, or the code it was left with. Nothing is decided here: every outline is read from
the saved arrays and the receipt; the planes' own pixels are read from the series, since a run keeps
only the middle slice's.
"""

import json
from collections.abc import Callable
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

from knee.objects.assignments import OBJECT_CODES

PANEL_INCH = 4.5


def window(plane: np.ndarray) -> np.ndarray:
    """The plane's pixels as grey, the 1st to the 99th percentile of what is finite."""
    values = np.asarray(plane, dtype=float)
    low, high = np.nanpercentile(values[np.isfinite(values)], (1, 99))
    return np.clip((values - low) / max(high - low, 1e-9), 0, 1)


def draw(
    run_dir: Path, study_uid: str, out: Path, volume_of: Callable[[str], np.ndarray]
) -> list[Path]:
    """One picture per profiled bone of every series of the study; returns their paths."""
    receipt = json.loads((run_dir / "receipt.json").read_text())
    records = [
        r for r in _records(receipt) if r.get("study_uid") == study_uid and "bones" in r
    ]
    out.mkdir(parents=True, exist_ok=True)
    drawn: list[Path] = []
    for record in records:
        arrays = np.load(run_dir / record["artifact"])
        volume = volume_of(record["series_uid"])
        for bone in ("femur", "tibia"):
            part = record["bones"].get(bone)
            if part is None:
                continue
            drawn.append(_picture(record, part, bone, arrays, volume, out))
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


def _picture(record, part, bone, arrays, volume, out: Path) -> Path:
    planes = part["pointed_planes"]
    count = max(1, len(planes))
    figure, axes = plt.subplots(
        1,
        count + 1,
        figsize=(PANEL_INCH * (count + 1), PANEL_INCH),
        squeeze=False,
    )
    axes = axes[0]
    area = arrays[f"a3_{bone}_profile_area_mm2"]
    position = arrays[f"a3_{bone}_depth_offsets_mm"]
    x = position if np.isfinite(position).all() else np.arange(len(area))
    axes[0].plot(x, area, "o-", ms=3, color="tab:blue")
    for slice_ in arrays[f"a3_{bone}_pointed_slices"]:
        axes[0].axvline(x[slice_], color="tab:red", lw=0.8)
    for z in np.flatnonzero(~np.isfinite(area)):
        axes[0].plot(
            [x[z]], [0], "kx", ms=4
        )  # not read, unreadable or cut: a gap, not zero
    axes[0].set_title(
        f"{bone} marrow-body area (mm2)\n{record['view']} outcome {part['outcome']}",
        fontsize=8,
    )
    axes[0].set_xlabel(
        "position along the stack's normal (mm); x = not read/unreadable/cut"
    )
    slices = list(arrays[f"a3_{bone}_plane_slices"])
    for axis, plane in zip(axes[1:], planes, strict=False):
        z = plane["slice"]
        axis.imshow(window(volume[z]), cmap="gray", interpolation="nearest")
        if plane["middle"]:
            region = arrays["a1_objects"] == OBJECT_CODES[bone]
        else:
            region = arrays[f"a3_{bone}_plane_region"][slices.index(z)]
        if region.any():
            axis.contour(region.astype(float), [0.5], colors="orange", linewidths=0.8)
        axis.set_title(
            f"slice {z} ({plane['position_mm']:.1f} mm){' middle' if plane['middle'] else ''}\n{plane['code']}",
            fontsize=8,
        )
        axis.axis("off")
    path = out / f"{record['series_uid'][-8:]}-{bone}.png"
    figure.savefig(path, dpi=100, bbox_inches="tight")
    plt.close(figure)
    return path
