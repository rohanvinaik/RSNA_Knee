"""The input stage's entry point: open the competition's files, and read a study whole."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from knee.study.decoders import require_decoders
from knee.study.series import Series, read_series
from knee.study.tables import SPLIT_FOLDER, SeriesRow, StudyRow, Tables, read_tables

LOCAL_ROOT = Path("data/raw")
# Where the kernel mounts the competition: measured by kaggle/decoder_probe, 2026-10-10.
KAGGLE_ROOT = Path("/kaggle/input/competitions/rsna-knee-abnormality-detection")


@dataclass(frozen=True, slots=True)
class Corpus:
    """The competition's files under `root`, in Kaggle's own layout, and its tables as given."""

    root: Path
    tables: Tables


@dataclass(frozen=True, slots=True)
class Study:
    """One study, whole: its row of the tables and each of its series, in the series table's order."""

    row: StudyRow
    series: tuple[Series, ...]


def open_corpus(root: Path) -> Corpus:
    """Refuse a missing decoder first, then read the tables. `root` is LOCAL_ROOT here, KAGGLE_ROOT in the kernel."""
    require_decoders()
    return Corpus(root=root, tables=read_tables(root))


def series_directory(corpus: Corpus, study: StudyRow, series: SeriesRow) -> Path:
    return (
        corpus.root / SPLIT_FOLDER[study.split] / series.study_uid / series.series_uid
    )


def read_study(corpus: Corpus, uid: str) -> Study:
    study = corpus.tables.studies[uid]
    return Study(
        row=study,
        series=tuple(
            read_series(series_directory(corpus, study, s), s) for s in study.series
        ),
    )
