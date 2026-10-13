"""The two objects and the seam between them.

Three things the lead had wrong and now does properly:
  - the leg is CLOSED (holes filled), not just outlined;
  - the superior-inferior axis is READ FROM THE HEADER, never assumed to be image rows;
  - the seam is found as a relation between two basins, not as a dark band hunted by intensity.
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


def closed_leg(plane):
    """Air is what touches the border; the leg is the rest, with its holes FILLED (gestalt
    closure: the thesis's stage 2 reasons from 'contiguous, closed')."""
    border = np.concatenate([plane[0], plane[-1], plane[:, 0], plane[:, -1]])
    level = float(np.quantile(border, 0.9)) * 2.0 + 1.0
    labels, _ = ndimage.label(plane <= level)
    touching = set(labels[0]) | set(labels[-1]) | set(labels[:, 0]) | set(labels[:, -1])
    touching.discard(0)
    outlined = ~np.isin(labels, list(touching))
    return ndimage.binary_fill_holes(outlined)


def superior_axis(geometry):
    """Which image axis runs superior-inferior, and which way is up. From the header, in LPS
    where superior is +Z. DICOM's ImageOrientationPatient is (row direction, column direction):
    moving along image axis 1 follows the row direction, along axis 0 the column direction."""
    row_dir = geometry.orientation[0][:3]
    col_dir = geometry.orientation[0][3:]
    if abs(col_dir[2]) >= abs(row_dir[2]):
        # image axis 0 (down the picture) carries superior-inferior
        return 0, (-1.0 if col_dir[2] > 0 else 1.0), float(col_dir[2])
    return 1, (-1.0 if row_dir[2] > 0 else 1.0), float(row_dir[2])


chosen = None
for uid in labeled:
    s = tables.studies[uid].series
    fs = [x for x in s if (x.anatomical_plane, x.fluid_sensitive) == ("Coronal", "1")]
    an = [x for x in s if (x.anatomical_plane, x.fluid_sensitive) == ("Coronal", "0")]
    if fs and an:
        a = read_series(
            ROOT / "train_series" / fs[0].study_uid / fs[0].series_uid, fs[0]
        )
        b = read_series(
            ROOT / "train_series" / an[0].study_uid / an[0].series_uid, an[0]
        )
        if a.volume is not None and b.volume is not None and a.geometry and b.geometry:
            chosen = (uid, [("fluid-sensitive", a), ("anatomy", b)])
            break

uid, pairs = chosen
fig, axes = plt.subplots(2, 4, figsize=(17, 8.6))

for row, (name, ser) in enumerate(pairs):
    vol = np.asarray(ser.volume, dtype=np.float64)
    mid = vol[vol.shape[0] // 2]
    hi = float(np.quantile(mid, 0.995))
    leg = closed_leg(mid)
    axis, sign, cosine = superior_axis(ser.geometry)

    axes[row, 0].imshow(np.where(leg, mid, np.nan), cmap="gray", vmin=0, vmax=hi)
    axes[row, 0].set_title(
        f"{name}: the CLOSED leg ({100 * leg.mean():.0f}%)\nS-I is image axis {axis}, Z cosine {cosine:+.2f}",
        fontsize=10,
    )

    # squint inside the leg, then the profile ALONG the header's superior-inferior axis
    tile = 6
    h, w = mid.shape
    hh, ww = h // tile * tile, w // tile * tile
    blocks = (
        mid[:hh, :ww].reshape(h // tile, tile, w // tile, tile).transpose(0, 2, 1, 3)
    )
    legb = leg[:hh, :ww].reshape(h // tile, tile, w // tile, tile).transpose(0, 2, 1, 3)
    inside = legb.reshape(h // tile, w // tile, -1).mean(2) > 0.5
    sq = np.where(
        inside, np.median(blocks.reshape(h // tile, w // tile, -1), axis=2), np.nan
    )

    axes[row, 1].imshow(sq, cmap="gray", vmin=0, vmax=hi)
    axes[row, 1].set_title(
        f"squinted {tile}x{tile}, inside the closed leg", fontsize=10
    )

    profile = np.nanmedian(np.where(inside, sq, np.nan), axis=1 - axis)
    if sign < 0:
        profile = profile[::-1]
    steps = np.arange(profile.size)
    axes[row, 2].plot(profile, steps, color="k")
    axes[row, 2].invert_yaxis()
    axes[row, 2].set_title(
        "median brightness ALONG the header's\nsuperior-inferior axis (superior at top)",
        fontsize=10,
    )

    # the two basins: watershed the negated squint for the anatomy weighting (bones bright),
    # the squint itself for fluid-sensitive (the SEAM is bright there, so the sign flips)
    field = sq if name == "anatomy" else -sq
    filled = np.where(np.isfinite(field), field, np.nanmin(field))
    smooth = ndimage.gaussian_filter(filled, 1.0)
    # two seeds, one each side of the seam, placed by the axis alone -- N = 2 is given
    seeds = np.zeros(smooth.shape, dtype=np.int32)
    n_along = smooth.shape[axis]
    sl_a = [slice(None), slice(None)]
    sl_b = [slice(None), slice(None)]
    sl_a[axis] = slice(0, n_along // 5)
    sl_b[axis] = slice(4 * n_along // 5, n_along)
    seeds[tuple(sl_a)] = 1
    seeds[tuple(sl_b)] = 2
    seeds[~inside] = 0
    from skimage.segmentation import watershed

    basins = watershed(-smooth, markers=seeds, mask=inside)
    axes[row, 3].imshow(basins, cmap="coolwarm", vmin=0, vmax=2)
    axes[row, 3].set_title(
        "two basins from two seeds placed by the axis\n(N = 2 is given by anatomy)",
        fontsize=10,
    )

    for c in (0, 1, 3):
        axes[row, c].set_xticks([])
        axes[row, c].set_yticks([])
    print(
        f"  {name:16s} leg {100 * leg.mean():5.1f}%  S-I axis {axis} sign {sign:+.0f} cos {cosine:+.3f}"
    )

plt.tight_layout()
plt.savefig(OUT / "seam.png", dpi=85, bbox_inches="tight")
print(f"wrote {OUT / 'seam.png'}  (study {uid[:12]})")
