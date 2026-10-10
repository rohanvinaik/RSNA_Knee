"""Is the third leg usable? The shape of the report column over the 58 labeled studies.

Not a reading of the reports -- a measurement of whether they exist, how long they are, and
whether they are machine-readable at all. Whether the report text can re-expand a folded
abstention is the founder's call to make on content; this only establishes whether there is
content to work with.
"""

from collections import Counter
from pathlib import Path

from knee.study.tables import labeled_uids, read_tables

ROOT = Path("data/raw")
tables = read_tables(ROOT)
labeled = sorted(labeled_uids(tables))

lengths = []
absent = 0
scripts: Counter = Counter()

for uid in labeled:
    report = tables.studies[uid].report
    if report is None or report.strip() == "":
        absent += 1
        continue
    lengths.append(len(report))
    # Which writing systems appear, as a crude language signal. Counted, never read.
    has_latin = any("a" <= c.lower() <= "z" for c in report)
    has_cyrillic = any("Ѐ" <= c <= "ӿ" for c in report)
    has_cjk = any("一" <= c <= "鿿" for c in report)
    has_arabic = any("؀" <= c <= "ۿ" for c in report)
    non_ascii_latin = any(c.isalpha() and ord(c) > 127 and "Ѐ" > c for c in report)
    marks = []
    if has_latin:
        marks.append("latin")
    if non_ascii_latin:
        marks.append("latin+diacritics")
    if has_cyrillic:
        marks.append("cyrillic")
    if has_cjk:
        marks.append("cjk")
    if has_arabic:
        marks.append("arabic")
    scripts["+".join(marks) if marks else "none"] += 1

print(f"labeled studies:        {len(labeled)}")
print(f"with a report:          {len(lengths)}")
print(f"with no report:         {absent}")
print()

if lengths:
    lengths.sort()
    print("report length, characters:")
    print(f"  min    {lengths[0]}")
    print(f"  p25    {lengths[len(lengths) // 4]}")
    print(f"  median {lengths[len(lengths) // 2]}")
    print(f"  p75    {lengths[3 * len(lengths) // 4]}")
    print(f"  max    {lengths[-1]}")
    print()

print("writing systems present (a crude language signal, counted not read):")
for k, n in scripts.most_common():
    print(f"  {k:28s} {n}")
print()

# How many findings are positive vs negative per study: the shape of what would be re-graded.
from knee.study.tables import LABELS

zeros_per_study: Counter = Counter()
for uid in labeled:
    labels = tables.studies[uid].labels
    zeros_per_study[sum(1 for f in LABELS if labels.get(f) == "0")] += 1

print("negatives per labeled study (the class that holds the folded abstentions):")
for n in sorted(zeros_per_study):
    print(f"  {n:2d} of 12 negative: {zeros_per_study[n]} studies")
total_zero = sum(k * v for k, v in zeros_per_study.items())
print(f"\n  total negative cells over the 58: {total_zero} of {58 * 12}")
