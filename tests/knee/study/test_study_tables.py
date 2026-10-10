"""The tables are read as given (knee.study.tables), on synthetic CSVs in Kaggle's schema."""

from __future__ import annotations

import csv
from pathlib import Path

import pytest

from knee.study.tables import (
    LABELS,
    SERIES_COLUMNS,
    TEST_COLUMNS,
    TRAIN_COLUMNS,
    labeled_uids,
    read_tables,
    split_uids,
)

REPORT = 'Synthetic report, with a comma,\na newline and "quotes".'


def write_csv(path: Path, columns: tuple[str, ...], rows: list[list[str]]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(columns)
        writer.writerows(rows)


def series_row(
    study: str, series: str, given: str = "1", plane: str = "Sagittal"
) -> list[str]:
    return [study, series, given, given, plane]


@pytest.fixture
def root(tmp_path: Path) -> Path:
    labels = ["1", "0"] * 6
    write_csv(
        tmp_path / "train.csv",
        TRAIN_COLUMNS,
        [
            ["s1", REPORT, *labels],
            ["s2", "unlabeled report", *([""] * 12)],
            ["s3", "odd report", *(["1.0"] + [""] * 11)],
        ],
    )
    write_csv(
        tmp_path / "train_series.csv",
        SERIES_COLUMNS,
        [
            series_row("s1", "a"),
            series_row("s1", "b", "0", "Axial"),
            series_row("s2", "c"),
            series_row("zz", "o"),
        ],
    )
    write_csv(tmp_path / "test.csv", TEST_COLUMNS, [["t1"]])
    write_csv(
        tmp_path / "test_series.csv",
        SERIES_COLUMNS,
        [series_row("t1", "d", "0", "Coronal")],
    )
    return tmp_path


def test_a_training_study_carries_its_report_and_label_codes_as_given(
    root: Path,
) -> None:
    study = read_tables(root).studies["s1"]
    assert study.split == "train"
    assert study.report == REPORT
    assert list(study.labels) == list(LABELS)
    assert list(study.labels.values()) == ["1", "0"] * 6
    assert [s.series_uid for s in study.series] == ["a", "b"]
    assert (study.series[1].fluid_sensitive, study.series[1].fat_suppression) == (
        "0",
        "0",
    )
    assert study.series[1].anatomical_plane == "Axial"


def test_blank_labels_are_not_given_and_odd_values_unrecognized(root: Path) -> None:
    tables = read_tables(root)
    assert set(tables.studies["s2"].labels.values()) == {"not_given"}
    assert tables.studies["s3"].labels["ACL"] == "unrecognized"


def test_a_test_study_has_no_report_and_no_labels(root: Path) -> None:
    study = read_tables(root).studies["t1"]
    assert (study.split, study.report, dict(study.labels)) == ("test", None, {})
    assert [s.series_uid for s in study.series] == ["d"]


def test_a_series_row_without_a_study_is_kept_not_dropped(root: Path) -> None:
    orphans = read_tables(root).orphan_series
    assert [(o.study_uid, o.series_uid) for o in orphans] == [("zz", "o")]


def test_only_fully_labeled_studies_are_labeled(root: Path) -> None:
    tables = read_tables(root)
    assert labeled_uids(tables) == ("s1",)
    assert split_uids(tables, "test") == ("t1",)
    assert split_uids(tables, "train") == ("s1", "s2", "s3")


def test_a_changed_header_is_refused(root: Path) -> None:
    write_csv(root / "test.csv", ("StudyInstanceUID", "Extra"), [["t1", "x"]])
    with pytest.raises(ValueError, match="columns"):
        read_tables(root)


def test_a_short_row_is_refused(root: Path) -> None:
    write_csv(root / "test_series.csv", SERIES_COLUMNS, [["t1", "d", "0"]])
    with pytest.raises(ValueError, match="cells"):
        read_tables(root)


def test_a_study_in_both_tables_is_refused(root: Path) -> None:
    write_csv(root / "test.csv", TEST_COLUMNS, [["s1"]])
    with pytest.raises(ValueError, match="twice"):
        read_tables(root)
