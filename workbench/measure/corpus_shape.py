"""What are we shown? The corpus's view structure, from the tables only (no pixel decode)."""

from collections import Counter
from pathlib import Path

from knee.study.tables import labeled_uids, read_tables

ROOT = Path("data/raw")

tables = read_tables(ROOT)
labeled = labeled_uids(tables)

print(f"studies in tables: {len(tables.studies)}")
print(f"labeled studies:   {len(labeled)}")
print(f"orphan series:     {len(tables.orphan_series)}")
print()

# A "view" is the triple the series table gives: plane, fluid sensitivity, fat suppression.
view_counts: Counter = Counter()
per_study_views: dict[str, Counter] = {}
series_per_study: Counter = Counter()

for uid in labeled:
    study = tables.studies[uid]
    series_per_study[len(study.series)] += 1
    views: Counter = Counter()
    for s in study.series:
        view = (s.anatomical_plane, s.fluid_sensitive, s.fat_suppression)
        view_counts[view] += 1
        views[view] += 1
    per_study_views[uid] = views

print("series per labeled study (count -> how many studies):")
for n in sorted(series_per_study):
    print(f"  {n:3d} series: {series_per_study[n]} studies")
print()

print("distinct views (plane, fluid_sensitive, fat_suppression) -> total series:")
for view, n in view_counts.most_common():
    in_studies = sum(1 for v in per_study_views.values() if v[view] > 0)
    print(f"  {view!s:60s} {n:4d} series, in {in_studies}/{len(labeled)} studies")
print()

# Which views does EVERY labeled study have?
universal = [v for v in view_counts if all(per_study_views[u][v] > 0 for u in labeled)]
print(f"views present in EVERY labeled study: {len(universal)}")
for v in universal:
    print(f"  {v}")
print()

# Marginals
print("anatomical_plane:")
for k, n in Counter(
    s.anatomical_plane for u in labeled for s in tables.studies[u].series
).most_common():
    print(f"  {k!r:30s} {n}")
print("fluid_sensitive:")
for k, n in Counter(
    s.fluid_sensitive for u in labeled for s in tables.studies[u].series
).most_common():
    print(f"  {k!r:30s} {n}")
print("fat_suppression:")
for k, n in Counter(
    s.fat_suppression for u in labeled for s in tables.studies[u].series
).most_common():
    print(f"  {k!r:30s} {n}")
print()

# Label prevalence: how many positive per finding
from knee.study.tables import LABELS

print("label prevalence over the labeled studies:")
for finding in LABELS:
    pos = sum(1 for u in labeled if tables.studies[u].labels.get(finding) == "1")
    neg = sum(1 for u in labeled if tables.studies[u].labels.get(finding) == "0")
    print(f"  {finding:28s} positive {pos:3d}  negative {neg:3d}")
