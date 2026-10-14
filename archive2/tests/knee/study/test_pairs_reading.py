"""Intent tests for the pairing orchestration (knee.study.pairs.read_pairs), both signs, over a
synthetic Study built from series rows alone. From the contract: a plane with one fat-bright and
one fat-dark series is paired; a plane with one series is solitary; a plane with three is surplus
and every series is kept; a fat-suppression flag `told_sign` cannot read counts as neither flavour;
a study with no series is `predecessor_empty`; planes keep first-appearance order and identifiers
keep table order; nothing but the table row is read; the ledger carries the two events."""

from __future__ import annotations

from pathlib import Path

from knee.study.corpus import Study
from knee.study.pairs import PAIR_CODES, AcquisitionPairs, read_pairs
from knee.study.series import read_series
from knee.study.tables import SeriesRow, StudyRow
from knee.telemetry import recording

STUDY_UID = "study-pairs"

#: A directory no series has: `read_series` then returns a Series with no slices, no volume and
#: no geometry, so every test below runs on the table rows alone and no header exists to read.
NOWHERE = Path("/nonexistent/the-funnel/pairs")


class _RowOnly:
    """A series stand-in that holds its table row and NOTHING else: any other attribute raises."""

    __slots__ = ("row",)

    def __init__(self, row: SeriesRow) -> None:
        self.row = row


def _row(uid: str, plane: str, fat: str, fluid: str = "0") -> SeriesRow:
    return SeriesRow(
        study_uid=STUDY_UID,
        series_uid=uid,
        fluid_sensitive=fluid,
        fat_suppression=fat,
        anatomical_plane=plane,
    )


def _study(*rows: tuple[str, str, str]) -> Study:
    """A study whose series are read by the stage's own reader from directories that do not exist."""
    series = tuple(
        read_series(NOWHERE / uid, _row(uid, plane, fat)) for uid, plane, fat in rows
    )
    return Study(
        row=StudyRow(
            uid=STUDY_UID,
            split="train",
            report="",
            labels={},
            series=tuple(s.row for s in series),
        ),
        series=series,
    )


# --- positive: what it must do -------------------------------------------------------------


def test_one_fat_bright_and_one_fat_dark_of_a_plane_are_the_pair() -> None:
    pairs = read_pairs(_study(("a", "Coronal", "0"), ("b", "Coronal", "1")))
    assert isinstance(pairs, AcquisitionPairs)
    assert pairs.study_uid == STUDY_UID
    assert pairs.code == "present"
    (pair,) = pairs.pairs
    assert pair.plane == "Coronal"
    assert pair.bright_uids == ("a",)
    assert pair.dark_uids == ("b",)
    assert pair.unreadable_uids == ()
    assert pair.code == "paired"


def test_a_plane_with_one_series_is_solitary_and_keeps_its_flavour() -> None:
    (pair,) = read_pairs(_study(("a", "Axial", "1"))).pairs
    assert pair.code == "solitary"
    assert pair.dark_uids == ("a",)
    assert pair.bright_uids == ()


def test_three_series_of_a_plane_are_surplus_and_all_three_are_kept() -> None:
    (pair,) = read_pairs(
        _study(("a", "Sagittal", "0"), ("b", "Sagittal", "1"), ("c", "Sagittal", "0"))
    ).pairs
    assert pair.code == "surplus"
    assert pair.bright_uids == ("a", "c")
    assert pair.dark_uids == ("b",)
    # Every series is kept; which two to lay over each other is not settled by the count.
    assert set(pair.bright_uids) | set(pair.dark_uids) == {"a", "b", "c"}


def test_an_unreadable_flag_counts_as_neither_flavour() -> None:
    (pair,) = read_pairs(
        _study(("a", "Coronal", "0"), ("b", "Coronal", "2"), ("c", "Coronal", ""))
    ).pairs
    assert pair.unreadable_uids == ("b", "c")
    assert pair.bright_uids == ("a",)
    assert pair.dark_uids == ()
    # One readable series: the plane is solitary, whatever the unreadable ones might have been.
    assert pair.code == "solitary"


def test_a_plane_whose_every_flag_is_unreadable_is_none_and_keeps_its_series() -> None:
    """`none` is reachable only this way: the plane is in the table, so it has a record, and
    every series of it counts as neither flavour. The series are kept, by identifier."""
    (pair,) = read_pairs(_study(("a", "Axial", "2"), ("b", "Axial", ""))).pairs
    assert pair.plane == "Axial"
    assert pair.code == "none"
    assert pair.unreadable_uids == ("a", "b")
    assert (pair.bright_uids, pair.dark_uids) == ((), ())


def test_an_empty_study_is_predecessor_empty_with_no_pairs() -> None:
    empty = Study(
        row=StudyRow(uid=STUDY_UID, split="train", report="", labels={}, series=()),
        series=(),
    )
    pairs = read_pairs(empty)
    assert pairs.code == "predecessor_empty"
    assert pairs.pairs == ()
    assert pairs.study_uid == STUDY_UID


def test_planes_keep_first_appearance_order_and_identifiers_keep_table_order() -> None:
    pairs = read_pairs(
        _study(
            ("a", "Sagittal", "0"),
            ("b", "Coronal", "1"),
            ("c", "Sagittal", "1"),
            ("d", "Coronal", "0"),
            ("e", "Axial", "1"),
        )
    )
    assert [pair.plane for pair in pairs.pairs] == ["Sagittal", "Coronal", "Axial"]
    assert [pair.code for pair in pairs.pairs] == ["paired", "paired", "solitary"]
    sagittal, coronal, _ = pairs.pairs
    assert (sagittal.bright_uids, sagittal.dark_uids) == (("a",), ("c",))
    assert (coronal.bright_uids, coronal.dark_uids) == (("d",), ("b",))


def test_the_ledger_carries_the_consumption_then_the_production_with_the_paired_count() -> (
    None
):
    study = _study(("a", "Coronal", "0"), ("b", "Coronal", "1"), ("c", "Axial", "1"))
    with recording() as run_ledger:
        read_pairs(study)
    events = run_ledger.events()
    assert [event.name for event in events] == [
        "study.consumed_by.pairs",
        "pairs.produced",
    ]
    assert dict(events[0].counts) == {"series": 3}
    assert dict(events[1].counts) == {"paired": 1}


def test_every_plane_code_is_in_the_vocabulary() -> None:
    pairs = read_pairs(
        _study(
            ("a", "Sagittal", "0"),
            ("b", "Sagittal", "1"),
            ("c", "Coronal", "1"),
            ("d", "Axial", "0"),
            ("e", "Axial", "0"),
            ("f", "Axial", "1"),
        )
    )
    assert all(pair.code in PAIR_CODES for pair in pairs.pairs)


# --- negative: what it must never do -------------------------------------------------------


def test_nothing_of_a_series_but_its_table_row_is_read() -> None:
    """MUST NOT: read a header, a slice, a volume or a description -- only the table's row."""
    rows = (_row("a", "Coronal", "0"), _row("b", "Coronal", "1"))
    study = Study(
        row=StudyRow(uid=STUDY_UID, split="train", report="", labels={}, series=rows),
        # Deliberately not a Series: the test is that nothing but `.row` is touched.
        series=tuple(_RowOnly(row) for row in rows),  # ty: ignore[invalid-argument-type]
    )
    (pair,) = read_pairs(study).pairs
    assert pair.code == "paired"
    assert (pair.bright_uids, pair.dark_uids) == (("a",), ("b",))


def test_a_pair_is_never_made_across_planes() -> None:
    pairs = read_pairs(_study(("a", "Sagittal", "0"), ("b", "Coronal", "1")))
    assert [pair.code for pair in pairs.pairs] == ["solitary", "solitary"]
    assert not any(pair.code == "paired" for pair in pairs.pairs)


def test_a_surplus_plane_pairs_nothing_even_with_one_of_each_flavour_present() -> None:
    (pair,) = read_pairs(
        _study(("a", "Axial", "0"), ("b", "Axial", "1"), ("c", "Axial", "1"))
    ).pairs
    assert pair.code != "paired"
    assert pair.code == "surplus"


def test_the_fluid_sensitive_flag_does_not_decide_the_flavour() -> None:
    """MUST NOT: read the flavour from the fluid-sensitive flag; it is the fat-suppression flag."""
    series = tuple(
        read_series(NOWHERE / uid, _row(uid, "Coronal", fat, fluid))
        for uid, fat, fluid in (("a", "0", "1"), ("b", "1", "1"))
    )
    study = Study(
        row=StudyRow(
            uid=STUDY_UID,
            split="train",
            report="",
            labels={},
            series=tuple(s.row for s in series),
        ),
        series=series,
    )
    (pair,) = read_pairs(study).pairs
    assert pair.code == "paired"
    assert (pair.bright_uids, pair.dark_uids) == (("a",), ("b",))
