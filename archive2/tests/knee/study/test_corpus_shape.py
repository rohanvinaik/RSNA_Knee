"""The corpus's shape from the tables alone, both signs (task 7.1a).

Built from `StudyRow` and `SeriesRow` records directly, so every count has a known answer. The
shape replaces the table-only probes; it counts and never judges.
"""

from types import MappingProxyType

from knee.study.codes import LABEL_CODES
from knee.study.shape import REPORT_CODES, CorpusShape, corpus_shape, report_code
from knee.study.tables import LABELS, SeriesRow, StudyRow, Tables


def _series(study: str, uid: str, plane: str, fluid: str, fat: str) -> SeriesRow:
    return SeriesRow(study, uid, fluid, fat, plane)


def _labels(value: str) -> dict[str, str]:
    return dict.fromkeys(LABELS, value)


def _tables() -> Tables:
    given = _labels("0")
    given["ACL"] = "1"
    given["Effusion"] = "1"
    studies = {
        "s1": StudyRow(
            "s1",
            "train",
            "a report of some length",
            given,
            (
                _series("s1", "a", "Sagittal", "1", "1"),
                _series("s1", "b", "Sagittal", "1", "1"),
                _series("s1", "c", "Coronal", "0", "0"),
            ),
        ),
        "s2": StudyRow(
            "s2",
            "train",
            "short",
            _labels("0"),
            (
                _series("s2", "d", "Sagittal", "1", "1"),
                _series("s2", "e", "Axial", "1", "1"),
            ),
        ),
        "s3": StudyRow("s3", "train", "", _labels("not_given"), ()),
        "s4": StudyRow(
            "s4",
            "train",
            "   ",
            {**_labels("0"), "MCL": "unrecognized"},
            (_series("s4", "f", "Coronal", "0", "0"),),
        ),
        "t1": StudyRow(
            "t1", "test", None, {}, (_series("t1", "g", "Axial", "1", "1"),)
        ),
    }
    return Tables(
        studies=MappingProxyType(studies),
        orphan_series=(_series("zz", "o", "Axial", "0", "0"),),
    )


# ---------------------------------------------------------------- positive


def test_the_shape_counts_studies_series_orphans_and_the_labeled() -> None:
    shape = corpus_shape(_tables())
    assert isinstance(shape, CorpusShape)
    assert dict(shape.studies) == {"train": 4, "test": 1}
    assert dict(shape.series) == {"train": 6, "test": 1}
    assert shape.orphan_series == 1
    assert shape.labeled == 2


def test_the_views_are_counted_over_the_labeled_studies_only() -> None:
    shape = corpus_shape(_tables())
    assert shape.views == (
        (("Sagittal", "1", "1"), 3, 2),
        (("Axial", "1", "1"), 1, 1),
        (("Coronal", "0", "0"), 1, 1),
    )
    assert dict(shape.views_per_labeled_study) == {2: 2}


def test_the_labels_are_counted_per_finding_over_the_training_studies() -> None:
    shape = corpus_shape(_tables())
    assert set(shape.labels) == set(LABELS)
    assert dict(shape.labels["ACL"]) == {
        "1": 1,
        "0": 2,
        "not_given": 1,
        "unrecognized": 0,
    }
    assert dict(shape.labels["MCL"]) == {
        "1": 0,
        "0": 2,
        "not_given": 1,
        "unrecognized": 1,
    }
    for finding in LABELS:
        assert tuple(shape.labels[finding]) == LABEL_CODES
        assert sum(shape.labels[finding].values()) == 4


def test_the_reports_are_measured_for_presence_and_length_never_read() -> None:
    shape = corpus_shape(_tables())
    assert dict(shape.reports) == {"present": 2, "blank": 2, "not_given": 0}
    assert shape.report_lengths == (5, 23, 23)


def test_report_code_names_text_blank_and_not_given_apart() -> None:
    assert report_code("a report") == "present"
    assert report_code("") == "blank"
    assert report_code("  \n") == "blank"
    assert report_code(None) == "not_given"
    for value in ("x", "", None, 3, object()):
        assert report_code(value) in REPORT_CODES


def test_an_empty_corpus_has_an_empty_shape_not_a_failure() -> None:
    shape = corpus_shape(Tables(studies=MappingProxyType({}), orphan_series=()))
    assert dict(shape.studies) == {} and shape.labeled == 0
    assert shape.views == () and shape.report_lengths == ()
    assert all(sum(counts.values()) == 0 for counts in shape.labels.values())


# ---------------------------------------------------------------- negative


def test_the_shape_is_read_only_and_counts_nothing_from_a_test_study_as_a_label() -> (
    None
):
    """MUST NOT: a test study has no labels and must not be counted as `not_given`; a mapping
    handed on must not be writable."""
    shape = corpus_shape(_tables())
    assert sum(shape.labels["ACL"].values()) == 4
    for mapping in (shape.studies, shape.labels, shape.labels["ACL"], shape.reports):
        try:
            mapping["x"] = 1  # type: ignore[index]
        except TypeError:
            continue
        raise AssertionError("a corpus-shape mapping was writable")


def test_no_field_of_the_shape_is_a_decision_or_names_anatomy() -> None:
    words = " ".join(CorpusShape.__slots__).lower()
    for word in ("femur", "tibia", "score", "threshold", "predict", "positive"):
        assert word not in words
