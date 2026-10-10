"""The competition's tables, read as given: every cell a raw string, a blank kept as a blank."""

from __future__ import annotations

import csv
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path

from knee.study.codes import label_code

LABELS: tuple[str, ...] = (
    "ACL",
    "MCL",
    "Medial Meniscus",
    "Lateral Meniscus",
    "Medial OA",
    "Lateral OA",
    "PF OA",
    "Effusion",
    "Synovitis",
    "Baker's",
    "Contusion",
    "Fracture",
)
TRAIN_COLUMNS: tuple[str, ...] = ("StudyInstanceUID", "Report", *LABELS)
SERIES_COLUMNS: tuple[str, ...] = (
    "StudyInstanceUID",
    "SeriesInstanceUID",
    "Fluid_Sensitive",
    "Fat_Suppression",
    "Anatomical_Plane",
)
TEST_COLUMNS: tuple[str, ...] = ("StudyInstanceUID",)
SPLIT_FOLDER: Mapping[str, str] = {"train": "train_series", "test": "test_series"}


@dataclass(frozen=True, slots=True)
class SeriesRow:
    """One row of train_series.csv or test_series.csv, every value as given."""

    study_uid: str
    series_uid: str
    fluid_sensitive: str
    fat_suppression: str
    anatomical_plane: str


@dataclass(frozen=True, slots=True)
class StudyRow:
    """One study as the tables give it.

    split: "train" or "test". report: a training study's report text, as given; None for a test study, for which the
    competition provides no report. labels: a training study's 12 findings, each as a label code
    (`codes.label_code`: "1", "0", "not_given" or "unrecognized"); empty for a test study, which has no labels.
    series: the study's rows of its split's series table, in the table's order.
    """

    uid: str
    split: str
    report: str | None
    labels: Mapping[str, str]
    series: tuple[SeriesRow, ...]


@dataclass(frozen=True, slots=True)
class Tables:
    """Every study of both splits, by StudyInstanceUID in table order, and any series row whose study is in neither
    study table (kept, never dropped)."""

    studies: Mapping[str, StudyRow]
    orphan_series: tuple[SeriesRow, ...]


def read_rows(path: Path, columns: tuple[str, ...]) -> list[dict[str, str]]:
    """Every row of a CSV as raw strings, refused unless its header is exactly `columns` and every row is whole."""
    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        if tuple(reader.fieldnames or ()) != columns:
            raise ValueError(
                f"{path.name}: the columns {reader.fieldnames} are not {list(columns)}"
            )
        rows = list(reader)
    for number, row in enumerate(rows, start=2):
        if None in row or any(value is None for value in row.values()):
            raise ValueError(
                f"{path.name}: line {number} does not have exactly {len(columns)} cells"
            )
    return rows


def read_series_rows(path: Path) -> list[SeriesRow]:
    return [
        SeriesRow(
            study_uid=r["StudyInstanceUID"],
            series_uid=r["SeriesInstanceUID"],
            fluid_sensitive=r["Fluid_Sensitive"],
            fat_suppression=r["Fat_Suppression"],
            anatomical_plane=r["Anatomical_Plane"],
        )
        for r in read_rows(path, SERIES_COLUMNS)
    ]


def read_tables(root: Path) -> Tables:
    """train.csv, train_series.csv, test.csv and test_series.csv under the competition root, as given."""
    series_of: dict[tuple[str, str], list[SeriesRow]] = {}
    for split, name in (("train", "train_series.csv"), ("test", "test_series.csv")):
        for row in read_series_rows(root / name):
            series_of.setdefault((split, row.study_uid), []).append(row)
    studies: dict[str, StudyRow] = {}
    for r in read_rows(root / "train.csv", TRAIN_COLUMNS):
        add_study(
            studies,
            StudyRow(
                uid=r["StudyInstanceUID"],
                split="train",
                report=r["Report"],
                labels={finding: label_code(r[finding]) for finding in LABELS},
                series=tuple(series_of.pop(("train", r["StudyInstanceUID"]), ())),
            ),
        )
    for r in read_rows(root / "test.csv", TEST_COLUMNS):
        add_study(
            studies,
            StudyRow(
                uid=r["StudyInstanceUID"],
                split="test",
                report=None,
                labels={},
                series=tuple(series_of.pop(("test", r["StudyInstanceUID"]), ())),
            ),
        )
    orphans = tuple(row for rows in series_of.values() for row in rows)
    return Tables(studies=studies, orphan_series=orphans)


def add_study(studies: dict[str, StudyRow], row: StudyRow) -> None:
    if row.uid in studies:
        raise ValueError(f"study {row.uid} appears twice in the study tables")
    studies[row.uid] = row


def labeled_uids(tables: Tables) -> tuple[str, ...]:
    """The training studies whose 12 labels are all given ("1" or "0"), in table order."""
    return tuple(
        uid
        for uid, study in tables.studies.items()
        if study.split == "train"
        and all(code in ("1", "0") for code in study.labels.values())
    )


def split_uids(tables: Tables, split: str) -> tuple[str, ...]:
    """The studies of one split ("train" or "test"), in table order."""
    return tuple(uid for uid, study in tables.studies.items() if study.split == split)
