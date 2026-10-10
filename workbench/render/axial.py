"""The axial stack through Z: where is the space between the two bones?

The founder: the view of the space between them is "the view of a single slice in Z, the axial
view, the slice taken in the middle". So walk the stack and look.
"""

from pathlib import Path

import matplotlib

from _out import pictures_dir

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from knee.study.series import read_series
from knee.study.tables import labeled_uids, read_tables

ROOT = Path("data/raw")
OUT = pictures_dir()
tables = read_tables(ROOT)
labeled = sorted(labeled_uids(tables))

picked = []
for uid in labeled:
    hit = [
        s
        for s in tables.studies[uid].series
        if (s.anatomical_plane, s.fluid_sensitive) == ("Axial", "1")
    ]
    if not hit:
        continue
    ser = read_series(
        ROOT / "train_series" / hit[0].study_uid / hit[0].series_uid, hit[0]
    )
    if (
        ser.volume is not None
        and ser.geometry is not None
        and ser.volume.shape[0] >= 12
    ):
        picked.append((uid, ser))
    if len(picked) == 2:
        break

n_show = 7
fig, axes = plt.subplots(len(picked), n_show, figsize=(3.0 * n_show, 3.3 * len(picked)))

for row, (uid, ser) in enumerate(picked):
    vol = np.asarray(ser.volume, dtype=np.float64)
    n = vol.shape[0]
    hi = float(np.quantile(vol, 0.995))
    # the stack is ordered ascending along its own normal; which way is superior?
    normal = ser.geometry.normal
    along = ser.geometry.along_normal
    superior_is_last = float(normal[2]) > 0
    idx = np.linspace(0, n - 1, n_show).astype(int)
    for c, i in enumerate(idx):
        axes[row, c].imshow(vol[i], cmap="gray", vmin=0, vmax=hi)
        pos = "mid" if c == n_show // 2 else ""
        axes[row, c].set_title(
            f"slice {i}/{n - 1}  {pos}\nz={along[i]:.0f}mm", fontsize=8
        )
        axes[row, c].set_xticks([])
        axes[row, c].set_yticks([])
    print(
        f"  {uid[:9]}  {n} slices  normal z {float(normal[2]):+.2f}  "
        f"superior is {'last' if superior_is_last else 'first'}  "
        f"extent {along[-1] - along[0]:.0f}mm"
    )

plt.tight_layout()
plt.savefig(OUT / "axial.png", dpi=80, bbox_inches="tight")
print(f"wrote {OUT / 'axial.png'}")
