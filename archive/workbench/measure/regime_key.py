"""The regime key, measured through Chapter 1's own reader.

Three facts the Chapter 2 design is blocked on:
  1. laterality  - is it recorded? the mirror step depends on it, and getting it wrong is fatal
                   for four of the 12 (medial/lateral meniscus, medial/lateral OA)
  2. on-disk     - how many studies actually have pixels here, vs rows in the tables
  3. signedness  - what the negative-valued series actually is (PixelRepresentation, ImageType)

Plus the zero share per series, which sorts the corpus into acquisition regimes.
One file per series, read with knee.study.slices.read_slice.
"""

from collections import Counter
from pathlib import Path

import numpy as np

from knee.study.slices import read_slice
from knee.study.tables import labeled_uids, read_tables

ROOT = Path("data/raw")
tables = read_tables(ROOT)
labeled = sorted(labeled_uids(tables))

# --- 2. How many studies have pixels on disk, over the WHOLE table ---
on_disk = {"train": 0, "test": 0}
absent = {"train": 0, "test": 0}
for study in tables.studies.values():
    folder = "train_series" if study.split == "train" else "test_series"
    has = any(
        (ROOT / folder / s.study_uid / s.series_uid).is_dir()
        and any((ROOT / folder / s.study_uid / s.series_uid).glob("*.dcm"))
        for s in study.series
    )
    (on_disk if has else absent)[study.split] += 1

print("=== studies with at least one series on disk ===")
for split in ("train", "test"):
    print(f"  {split}: {on_disk[split]} on disk, {absent[split]} absent")
print()

# --- 1 + 3 + zero share: one file per series of the 58 ---
lat_tags = Counter()
lat_values = Counter()
image_types = Counter()
pixel_repr = Counter()
signed_series = []
zero_shares = []

for uid in labeled:
    study = tables.studies[uid]
    for s in study.series:
        directory = ROOT / "train_series" / s.study_uid / s.series_uid
        paths = sorted(directory.glob("*.dcm"))
        if not paths:
            continue
        sl = read_slice(paths[len(paths) // 2])
        h = sl.header

        # laterality: (0020,0060) Laterality, (0020,0062) ImageLaterality
        got = []
        for name in ("Laterality", "ImageLaterality", "FrameLaterality"):
            v = getattr(h, name, None)
            if v not in (None, ""):
                got.append(name)
                lat_values[f"{name}={v}"] += 1
        lat_tags["+".join(got) if got else "NONE"] += 1

        it = getattr(h, "ImageType", None)
        image_types[tuple(it)[:4] if it is not None else "ABSENT"] += 1
        pr = getattr(h, "PixelRepresentation", None)
        pixel_repr[pr] += 1

        px = sl.pixels
        zero_shares.append(float((px == 0).mean()))
        if px.min() < 0:
            signed_series.append(
                (
                    uid[:10],
                    s.anatomical_plane,
                    f"PixelRepresentation={pr}",
                    f"ImageType={tuple(it) if it is not None else 'ABSENT'}",
                    f"range {px.min()}..{px.max()}",
                )
            )

print("=== laterality: which tags carry it (one file per series, 58 studies) ===")
for k, n in lat_tags.most_common():
    print(f"  {k:40s} {n}")
print("  values:")
for k, n in lat_values.most_common(10):
    print(f"    {k:38s} {n}")
print()

print("=== PixelRepresentation (0 unsigned, 1 signed) ===")
for k, n in pixel_repr.most_common():
    print(f"  {k}: {n}")
print()

print("=== ImageType, first four values ===")
for k, n in image_types.most_common(10):
    print(f"  {k!s:60s} {n}")
print()

print(f"=== series with negative stored values: {len(signed_series)} ===")
for row in signed_series[:10]:
    print("  " + " | ".join(row))
print()

z = np.array(zero_shares)
print("=== zero share per series ===")
print(f"  n={z.size}  min {z.min():.4f}  median {np.median(z):.4f}  max {z.max():.4f}")
for lo, hi in ((0.0, 0.001), (0.001, 0.01), (0.01, 0.05), (0.05, 0.2), (0.2, 1.01)):
    print(f"  [{lo:.3f}, {hi:.3f}): {int(((z >= lo) & (z < hi)).sum())} series")
