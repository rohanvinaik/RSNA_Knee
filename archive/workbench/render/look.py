"""LOOK at the knees. What is actually in these images, and what is my split calling background?

Not a metric. A picture. For each of several series across the views: the middle slice as recorded,
what the current background split calls quiet, the histogram with the split marked, and the squint.
"""

from pathlib import Path

import matplotlib

from _out import pictures_dir

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from knee.collapse.noise import background_split, finite_values
from knee.study.series import read_series
from knee.study.tables import labeled_uids, read_tables

ROOT = Path("data/raw")
OUT = pictures_dir()

tables = read_tables(ROOT)
labeled = sorted(labeled_uids(tables))

# one series per view, from the first studies that have it
wanted = [
    ("Sagittal", "1", "1"),
    ("Coronal", "1", "1"),
    ("Axial", "1", "1"),
    ("Sagittal", "0", "0"),
]
picked: list = []
for view in wanted:
    for uid in labeled:
        hit = [
            s
            for s in tables.studies[uid].series
            if (s.anatomical_plane, s.fluid_sensitive, s.fat_suppression) == view
        ]
        if not hit:
            continue
        d = ROOT / "train_series" / hit[0].study_uid / hit[0].series_uid
        ser = read_series(d, hit[0])
        if ser.volume is None:
            continue
        picked.append((view, uid, ser))
        break

fig, axes = plt.subplots(len(picked), 4, figsize=(17, 4.2 * len(picked)))
if len(picked) == 1:
    axes = axes[None, :]

for row, (view, _uid, ser) in enumerate(picked):
    vol = np.asarray(ser.volume, dtype=np.float64)
    mid = vol[vol.shape[0] // 2]
    vals = finite_values(vol)
    split = background_split(vals)

    hi = float(np.quantile(mid, 0.995))
    axes[row, 0].imshow(mid, cmap="gray", vmin=0, vmax=hi)
    axes[row, 0].set_title(f"{view[0]} fs={view[1]}  as recorded", fontsize=9)

    # what the split calls quiet, in red over the image
    quiet_mask = mid <= split if np.isfinite(split) else np.zeros_like(mid, dtype=bool)
    rgb = np.dstack([mid / max(hi, 1)] * 3).clip(0, 1)
    rgb[quiet_mask] = [1.0, 0.25, 0.25]
    axes[row, 1].imshow(rgb)
    axes[row, 1].set_title(
        f"red = what the split calls BACKGROUND\nsplit={split:.0f}, {100 * quiet_mask.mean():.0f}% of this slice",
        fontsize=9,
    )

    axes[row, 2].hist(vals, bins=300, range=(0, hi * 1.5), color="0.3")
    if np.isfinite(split):
        axes[row, 2].axvline(split, color="red", lw=2)
    axes[row, 2].set_yscale("log")
    axes[row, 2].set_title("histogram of the whole volume (log)", fontsize=9)

    # the squint: 8x8 tile medians
    tile = 8
    h, w = mid.shape
    cut = mid[: h // tile * tile, : w // tile * tile]
    squint = np.median(
        cut.reshape(h // tile, tile, w // tile, tile)
        .transpose(0, 2, 1, 3)
        .reshape(h // tile, w // tile, -1),
        axis=2,
    )
    axes[row, 3].imshow(squint, cmap="gray", vmin=0, vmax=hi)
    axes[row, 3].set_title(f"the squint: {tile}x{tile} tile medians", fontsize=9)

    for c in range(4):
        axes[row, c].set_xticks([])
        axes[row, c].set_yticks([])

plt.tight_layout()
plt.savefig(OUT / "look.png", dpi=85, bbox_inches="tight")
print(f"wrote {OUT / 'look.png'}")
for view, uid, ser in picked:
    vals = finite_values(np.asarray(ser.volume, dtype=np.float64))
    print(
        f"  {view!s:28s} {uid[:9]}  vol {ser.volume.shape}  "
        f"split {background_split(vals):8.1f}  p50 {np.median(vals):7.1f}  max {vals.max():8.1f}"
    )
