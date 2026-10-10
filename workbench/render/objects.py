"""Two objects that combine: can the femur and the tibia be resolved, and the space between them?

The question is not whether a threshold separates them. It is whether they are THERE as objects --
two large bodies, one above the other, with a space between where they meet. Shown on both
weightings of the same study, because the marrow's sign flips between them while cortical bone is
signal-void on both.
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


def leg_mask(plane):
    border = np.concatenate([plane[0], plane[-1], plane[:, 0], plane[:, -1]])
    level = float(np.quantile(border, 0.9)) * 2.0 + 1.0
    labels, _ = ndimage.label(plane <= level)
    touching = set(labels[0]) | set(labels[-1]) | set(labels[:, 0]) | set(labels[:, -1])
    touching.discard(0)
    return ~np.isin(labels, list(touching))


# one study that carries BOTH a coronal fluid-sensitive and a coronal anatomy series
chosen = None
for uid in labeled:
    series = tables.studies[uid].series
    fs = [
        s for s in series if (s.anatomical_plane, s.fluid_sensitive) == ("Coronal", "1")
    ]
    an = [
        s for s in series if (s.anatomical_plane, s.fluid_sensitive) == ("Coronal", "0")
    ]
    if fs and an:
        a = read_series(
            ROOT / "train_series" / fs[0].study_uid / fs[0].series_uid, fs[0]
        )
        b = read_series(
            ROOT / "train_series" / an[0].study_uid / an[0].series_uid, an[0]
        )
        if a.volume is not None and b.volume is not None:
            chosen = (uid, [("fluid-sensitive", a), ("anatomy", b)])
            break

uid, pairs = chosen
fig, axes = plt.subplots(2, 4, figsize=(17, 8.6))

for row, (name, ser) in enumerate(pairs):
    vol = np.asarray(ser.volume, dtype=np.float64)
    mid = vol[vol.shape[0] // 2]
    hi = float(np.quantile(mid, 0.995))
    leg = leg_mask(mid)

    axes[row, 0].imshow(mid, cmap="gray", vmin=0, vmax=hi)
    axes[row, 0].set_title(f"{name}: as recorded", fontsize=10)

    # squint, inside the leg only
    tile = 6
    h, w = mid.shape
    cut = mid[: h // tile * tile, : w // tile * tile]
    legc = leg[: h // tile * tile, : w // tile * tile]
    blocks = cut.reshape(h // tile, tile, w // tile, tile).transpose(0, 2, 1, 3)
    legb = legc.reshape(h // tile, tile, w // tile, tile).transpose(0, 2, 1, 3)
    sq = np.where(
        legb.reshape(*blocks.shape[:2], -1).mean(2) > 0.5,
        np.median(blocks.reshape(*blocks.shape[:2], -1), axis=2),
        np.nan,
    )
    axes[row, 1].imshow(sq, cmap="gray", vmin=0, vmax=hi)
    axes[row, 1].set_title(f"squinted {tile}x{tile}, inside the leg", fontsize=10)

    # cortical bone is signal-void on BOTH weightings: the darkest places inside the leg
    inside = sq[np.isfinite(sq)]
    dark_level = float(np.quantile(inside, 0.20))
    axes[row, 2].imshow(
        np.where(np.isfinite(sq), sq <= dark_level, np.nan), cmap="viridis"
    )
    axes[row, 2].set_title(
        "the darkest fifth inside the leg\n(cortical bone is void on both)", fontsize=10
    )

    # the two largest bodies that are NOT that dark: the marrow of two bones, on fs=0
    bright = np.where(np.isfinite(sq), sq > dark_level, False)
    lab, n = ndimage.label(bright)
    sizes = ndimage.sum(bright, lab, range(1, n + 1))
    order = np.argsort(sizes)[::-1]
    shown = np.zeros_like(lab)
    for rank, idx in enumerate(order[:3], start=1):
        shown[lab == idx + 1] = rank
    axes[row, 3].imshow(shown, cmap="tab10", vmin=0, vmax=10)
    axes[row, 3].set_title(
        f"the 3 largest connected bodies above it\n{n} bodies in all", fontsize=10
    )

    for c in range(4):
        axes[row, c].set_xticks([])
        axes[row, c].set_yticks([])
    print(
        f"  {name:16s} leg {100 * leg.mean():.0f}%  bodies {n}  3 largest {sizes[order[:3]]}"
    )

plt.tight_layout()
plt.savefig(OUT / "objects.png", dpi=85, bbox_inches="tight")
print(f"wrote {OUT / 'objects.png'}  (study {uid[:12]})")
