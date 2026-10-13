"""The structural reading: air is what touches the border, the leg is what does not.

Not a threshold. Air is defined by CONNECTIVITY to the frame's edge, which is what the images
plainly show. Then: does the joint line survive the squint, and where does the population of
studies actually disagree?
"""

from pathlib import Path

import matplotlib

from _out import pictures_dir

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from scipy import ndimage

from knee.study.series import read_series
from knee.study.tables import labeled_uids, read_tables

ROOT = Path("data/raw")
OUT = pictures_dir()

tables = read_tables(ROOT)
labeled = sorted(labeled_uids(tables))


def air_by_connectivity(plane, seed_quantile=0.5):
    """Air = low-value places CONNECTED TO THE BORDER. The level only has to be loose enough to
    include air and tight enough to exclude the leg's interior; connectivity does the real work,
    so the exact level stops mattering."""
    border = np.concatenate([plane[0], plane[-1], plane[:, 0], plane[:, -1]])
    level = float(np.quantile(border, 0.9)) * 2.0 + 1.0
    low = plane <= level
    labels, _ = ndimage.label(low)
    touching = set(labels[0]) | set(labels[-1]) | set(labels[:, 0]) | set(labels[:, -1])
    touching.discard(0)
    return np.isin(labels, list(touching)), level


wanted = [("Sagittal", "1", "1"), ("Coronal", "1", "1"), ("Sagittal", "0", "0")]
picked = []
for view in wanted:
    for uid in labeled:
        hit = [
            s
            for s in tables.studies[uid].series
            if (s.anatomical_plane, s.fluid_sensitive, s.fat_suppression) == view
        ]
        if not hit:
            continue
        ser = read_series(
            ROOT / "train_series" / hit[0].study_uid / hit[0].series_uid, hit[0]
        )
        if ser.volume is not None:
            picked.append((view, ser))
            break

fig, axes = plt.subplots(len(picked), 4, figsize=(17, 4.3 * len(picked)))
for row, (view, ser) in enumerate(picked):
    vol = np.asarray(ser.volume, dtype=np.float64)
    mid = vol[vol.shape[0] // 2]
    hi = float(np.quantile(mid, 0.995))

    air, level = air_by_connectivity(mid)
    leg = ~air

    rgb = np.dstack([mid / max(hi, 1)] * 3).clip(0, 1)
    rgb[air] = [1.0, 0.25, 0.25]
    axes[row, 0].imshow(rgb)
    axes[row, 0].set_title(
        f"{view[0]} fs={view[1]}\nred = AIR, by connection to the border ({100 * air.mean():.0f}%)",
        fontsize=9,
    )

    # the noise population is the air, and it is a WHOLE population
    in_air = mid[air]
    axes[row, 1].hist(in_air, bins=120, color="crimson")
    axes[row, 1].set_yscale("log")
    axes[row, 1].set_title(
        f"the air's own values: n={in_air.size}\nmed {np.median(in_air):.0f}  p99 {np.quantile(in_air, 0.99):.0f}",
        fontsize=9,
    )

    # the leg, squinted, with the vertical profile beside it
    tile = 8
    h, w = mid.shape
    cut = (mid * leg)[: h // tile * tile, : w // tile * tile]
    sq = np.median(
        cut.reshape(h // tile, tile, w // tile, tile)
        .transpose(0, 2, 1, 3)
        .reshape(h // tile, w // tile, -1),
        axis=2,
    )
    axes[row, 2].imshow(sq, cmap="gray", vmin=0, vmax=hi)
    axes[row, 2].set_title(f"the leg, squinted {tile}x{tile}", fontsize=9)

    # the darkest ROW of the squinted leg: the joint line is a dark band across the bone
    inside = sq[:, sq.shape[1] // 4 : 3 * sq.shape[1] // 4]
    profile = np.array(
        [np.median(r[r > 0]) if np.any(r > 0) else np.nan for r in inside]
    )
    axes[row, 3].plot(profile, np.arange(profile.size), color="k")
    axes[row, 3].invert_yaxis()
    if np.any(np.isfinite(profile)):
        axes[row, 3].axhline(int(np.nanargmin(profile)), color="red", lw=2)
    axes[row, 3].set_title(
        "median brightness down the centre\nred = the darkest band", fontsize=9
    )
    axes[row, 3].set_ylim(profile.size, 0)

    for c in (0, 2):
        axes[row, c].set_xticks([])
        axes[row, c].set_yticks([])
    print(
        f"  {view!s:26s} air level {level:7.1f}  air {100 * air.mean():5.1f}%  "
        f"air n={in_air.size:7d}  air med {np.median(in_air):6.1f}  leg {100 * leg.mean():5.1f}%"
    )

plt.tight_layout()
plt.savefig(OUT / "structure.png", dpi=85, bbox_inches="tight")
print(f"wrote {OUT / 'structure.png'}")
