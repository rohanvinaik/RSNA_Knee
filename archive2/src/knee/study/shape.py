"""THE CORPUS'S SHAPE, read from the tables alone: what we are shown, counted and never judged.

Task 7.1a of `every-stage-renders`. This replaces the table-only probes `corpus_shape.py`,
`reports.py` and the laterality and on-disk parts of `regime_key.py` in `workbench/measure/`,
which each read the tables by hand and printed. The founder: *"I don't run ANY by hand. ALL
probes are supposed to be part of production."* So the one command reads the corpus's shape once
when it opens the corpus, writes it in the receipt, and draws it.

Everything here is a COUNT over the tables as given (`knee.study.tables`): how many studies each
split holds, which view triples the labeled studies carry and how widely, how the twelve labels
are distributed over the training studies, and whether the report column exists and how long it
runs. Counts of labels are information about the corpus and are read by nothing in the route: no
stage consults a label or a prevalence (project law 4), and this record is the place a reader looks
to know what the corpus is, never a place a decision looks. No pixel is decoded and no file is
opened: the shape is the tables'.
"""

from __future__ import annotations

from collections import Counter
from collections.abc import Mapping
from dataclasses import dataclass
from types import MappingProxyType

from knee.study.codes import LABEL_CODES
from knee.study.tables import LABELS, Tables, labeled_uids

#: What the report column holds for one training study.
REPORT_CODES: tuple[str, ...] = ("present", "blank", "not_given")


@dataclass(frozen=True, slots=True)
class CorpusShape:
    """The corpus's shape as counts, every mapping read-only.

    studies: studies per split. series: series rows per split, orphans excluded. orphan_series:
    series rows whose study is in neither study table. labeled: training studies whose twelve
    labels are all given. views: one entry per view triple (plane, fluid-sensitive, fat-suppressed)
    seen on a labeled study: the triple, how many series carry it over the labeled studies, and
    how many labeled studies carry at least one; ordered by studies then series, descending, then
    by the triple. views_per_labeled_study: how many distinct triples a labeled study carries, to
    how many labeled studies carry that many. labels: per finding, each label code's count over
    the TRAINING studies (`knee.study.codes.LABEL_CODES`). reports: per report code, the count of
    training studies; report_lengths: the shortest, the median and the longest present report in
    characters, or () when none is present.
    """

    studies: Mapping[str, int]
    series: Mapping[str, int]
    orphan_series: int
    labeled: int
    views: tuple[tuple[tuple[str, str, str], int, int], ...]
    views_per_labeled_study: Mapping[int, int]
    labels: Mapping[str, Mapping[str, int]]
    reports: Mapping[str, int]
    report_lengths: tuple[int, int, int] | tuple[()]


def report_code(report: object) -> str:
    """What the report column holds: text, a blank, or nothing given (a test study).

    post: __return__ in REPORT_CODES
    """
    if report is None:
        return "not_given"
    if isinstance(report, str) and report.strip():
        return "present"
    return "blank"


def _frozen(mapping: dict) -> Mapping:
    return MappingProxyType(dict(mapping))


def corpus_shape(tables: Tables) -> CorpusShape:
    """Count the corpus's shape from the tables as given. Pure over the tables; decides nothing."""
    studies: Counter[str] = Counter()
    series: Counter[str] = Counter()
    for study in tables.studies.values():
        studies[study.split] += 1
        series[study.split] += len(study.series)
    labeled = labeled_uids(tables)
    series_by_view: Counter[tuple[str, str, str]] = Counter()
    studies_by_view: Counter[tuple[str, str, str]] = Counter()
    distinct_per_study: Counter[int] = Counter()
    for uid in labeled:
        triples = [
            (s.anatomical_plane, s.fluid_sensitive, s.fat_suppression)
            for s in tables.studies[uid].series
        ]
        series_by_view.update(triples)
        studies_by_view.update(set(triples))
        distinct_per_study[len(set(triples))] += 1
    views = tuple(
        sorted(
            (
                (triple, series_by_view[triple], studies_by_view[triple])
                for triple in series_by_view
            ),
            key=lambda item: (-item[2], -item[1], item[0]),
        )
    )
    labels: dict[str, Mapping[str, int]] = {}
    for finding in LABELS:
        counts = Counter({code: 0 for code in LABEL_CODES})
        for study in tables.studies.values():
            if study.split == "train":
                counts[study.labels.get(finding, "not_given")] += 1
        labels[finding] = _frozen(counts)
    reports = Counter({code: 0 for code in REPORT_CODES})
    lengths: list[int] = []
    for study in tables.studies.values():
        if study.split != "train":
            continue
        code = report_code(study.report)
        reports[code] += 1
        if code == "present" and isinstance(study.report, str):
            lengths.append(len(study.report))
    lengths.sort()
    report_lengths: tuple[int, int, int] | tuple[()] = (
        (lengths[0], lengths[len(lengths) // 2], lengths[-1]) if lengths else ()
    )
    return CorpusShape(
        studies=_frozen(studies),
        series=_frozen(series),
        orphan_series=len(tables.orphan_series),
        labeled=len(labeled),
        views=views,
        views_per_labeled_study=_frozen(distinct_per_study),
        labels=_frozen(labels),
        reports=_frozen(reports),
        report_lengths=report_lengths,
    )
