"""Run the regime key over every series of the 58, through Chapter 1's real entry point.

The first test of stages 1 and 2 on real data: until now the noise law has only seen synthetic
draws. Reports the per-series table and the distributions of each word.
"""

import sys
from collections import Counter
from pathlib import Path

import numpy as np

from knee.collapse.regime import read_regime
from knee.study.series import read_series
from knee.study.tables import labeled_uids, read_tables

ROOT = Path("data/raw")
tables = read_tables(ROOT)
labeled = sorted(labeled_uids(tables))

rows = []
refused = 0
for i, uid in enumerate(labeled):
    study = tables.studies[uid]
    for s in study.series:
        directory = ROOT / "train_series" / s.study_uid / s.series_uid
        try:
            series = read_series(directory, s)
        except Exception as exc:
            print(f"  READ FAILED {uid[:10]} {type(exc).__name__}: {str(exc)[:60]}")
            continue
        key = read_regime(series)
        if key is None:
            refused += 1
            continue
        rows.append(key)
    print(
        f"\r  {i + 1}/{len(labeled)} studies, {len(rows)} series read",
        end="",
        file=sys.stderr,
    )

print(
    f"\n\nseries with a regime key: {len(rows)}; refused (no stacked volume): {refused}\n"
)


def spread(name, values):
    vals = np.array([v for v in values if np.isfinite(v)])
    if vals.size == 0:
        print(f"  {name:20s} none finite")
        return
    q = np.quantile(vals, (0, 0.25, 0.5, 0.75, 1.0))
    print(
        f"  {name:20s} n={vals.size:3d}  min {q[0]:9.3f}  p25 {q[1]:9.3f}  "
        f"med {q[2]:9.3f}  p75 {q[3]:9.3f}  max {q[4]:9.3f}"
    )


print("=== the words ===")
for field in ("quiet", "coils_word", "concurrence", "storage", "normalization"):
    counts = Counter(getattr(r, field) for r in rows)
    print(f"  {field}:")
    for k, n in counts.most_common():
        print(f"      {k:24s} {n:4d}  ({100 * n / len(rows):.1f}%)")

print("\n=== the noise law ===")
spread("dark sigma", [r.dark for r in rows])
spread("bright sigma", [r.bright for r in rows])
spread("bright/dark ratio", [r.bright / r.dark for r in rows if r.dark > 0])
spread("coils", [r.coils for r in rows])

print("\n=== the cheap global readings ===")
spread("zero share", [r.zero_share for r in rows])
spread("foreground share", [r.foreground_share for r in rows])
spread("tercile low", [r.terciles[0] for r in rows])
spread("tercile high", [r.terciles[1] for r in rows])
spread("tercile width", [r.terciles[1] - r.terciles[0] for r in rows])
spread("spread ratio", [r.spread_ratio for r in rows])
spread("skew", [r.skew for r in rows])
spread("depth spread", [r.depth_spread for r in rows])

print("\n=== foreground share by view (the knee's density) ===")
by_view = {}
for r in rows:
    by_view.setdefault(r.view, []).append(r.foreground_share)
for view in sorted(by_view, key=lambda v: -len(by_view[v])):
    vals = np.array(by_view[view])
    print(
        f"  {view!s:28s} n={vals.size:3d}  "
        f"med {np.median(vals):.3f}  min {vals.min():.3f}  max {vals.max():.3f}"
    )

print("\n=== does the tercile band move with composition? ===")
# Within one view, the tercile width in units of the series' own dark sigma. If the band is a
# stable property of the anatomy, this is tight; if it tracks composition, it is wide.
for view in sorted(by_view, key=lambda v: -len(by_view[v]))[:3]:
    same = [
        r for r in rows if r.view == view and r.dark > 0 and np.isfinite(r.terciles[0])
    ]
    if len(same) < 5:
        continue
    width = np.array([(r.terciles[1] - r.terciles[0]) / r.dark for r in same])
    fg = np.array([r.foreground_share for r in same])
    corr = float(np.corrcoef(width, fg)[0, 1]) if width.size > 2 else float("nan")
    print(
        f"  {view!s:28s} n={len(same):3d}  band width in dark sigmas: "
        f"med {np.median(width):7.2f}  spread {np.std(width):7.2f}  "
        f"corr with foreground share {corr:+.3f}"
    )
