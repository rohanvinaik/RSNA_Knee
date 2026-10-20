import csv
from decimal import Decimal
from pathlib import Path

import pytest

from knee.diagnosis.submission import (
    SUBMISSION_COLUMNS,
    SubmissionError,
    validate_submission,
    write_submission,
)
from knee.study.tables import LABELS

OFFICIAL_TEMPLATE_COLUMNS = (
    "StudyInstanceUID",
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


@pytest.fixture(scope="module")
def template(tmp_path_factory) -> Path:
    path = tmp_path_factory.mktemp("submission-template") / "sample_submission.csv"
    with path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.writer(stream)
        writer.writerow(OFFICIAL_TEMPLATE_COLUMNS)
        for uid in ("study-a", "study-b", "study-c"):
            writer.writerow((uid, *("0" for _ in OFFICIAL_TEMPLATE_COLUMNS[1:])))
    return path


def _template_uids(template: Path) -> list[str]:
    with template.open(newline="", encoding="utf-8") as stream:
        reader = csv.reader(stream)
        header = next(reader)
        assert tuple(header) == SUBMISSION_COLUMNS
        return [row[0] for row in reader]


def _row(value: float | Decimal = 0.5) -> dict[str, int | float | Decimal]:
    return {label: value for label in LABELS}


def test_write_submission_uses_template_order_and_explicit_probabilities(
    tmp_path, template
):
    uids = _template_uids(template)
    rows = [
        (uid, _row(Decimal(index) / Decimal(2)))
        for index, uid in reversed(list(enumerate(uids)))
    ]
    output = tmp_path / "submission.csv"

    receipt = write_submission(
        template,
        output,
        rows,
        source_provenance={
            "kind": "caller-supplied",
            "source_path": "/evidence/rows.json",
        },
    )

    with output.open(newline="", encoding="utf-8") as stream:
        actual = list(csv.reader(stream))
    assert tuple(actual[0]) == SUBMISSION_COLUMNS
    assert [row[0] for row in actual[1:]] == uids
    assert actual[1][1:] == ["0", "0", "0", "0", "0", "0", "0", "0", "0", "0", "0", "0"]
    assert actual[-1][1:] == [
        "1",
        "1",
        "1",
        "1",
        "1",
        "1",
        "1",
        "1",
        "1",
        "1",
        "1",
        "1",
    ]
    assert receipt["study_count"] == len(uids)
    assert receipt["source_provenance"]["source_path"] == "/evidence/rows.json"
    assert (
        validate_submission(template, output)["submission_sha256"]
        == receipt["submission_sha256"]
    )


def test_two_supplied_signs_are_written_as_supplied_without_mapping(tmp_path, template):
    uids = _template_uids(template)
    output = tmp_path / "submission.csv"
    rows = [(uid, _row(0.25 if index == 0 else 0.75)) for index, uid in enumerate(uids)]

    write_submission(
        template,
        output,
        rows,
        source_provenance={"decision": "values supplied by caller"},
    )

    with output.open(newline="", encoding="utf-8") as stream:
        actual = list(csv.reader(stream))
    assert actual[1][1:] == ["0.25"] * len(LABELS)
    assert actual[2][1:] == ["0.75"] * len(LABELS)


@pytest.mark.parametrize(
    ("rows", "code"),
    [
        (lambda uids: [(uids[0], _row())], "probability_study_uid_missing"),
        (
            lambda uids: [(uid, _row()) for uid in uids] + [("extra-study", _row())],
            "probability_study_uid_extra",
        ),
        (
            lambda uids: [(uid, _row()) for uid in uids] + [(uids[0], _row())],
            "probability_study_uid_duplicate",
        ),
    ],
)
def test_writer_requires_exact_unique_study_coverage(tmp_path, template, rows, code):
    output = tmp_path / "submission.csv"
    with pytest.raises(SubmissionError) as caught:
        write_submission(
            template,
            output,
            rows(_template_uids(template)),
            source_provenance={"kind": "test"},
        )
    assert caught.value.code == code
    assert not output.exists()


@pytest.mark.parametrize(
    ("values", "code"),
    [
        ({**_row(), "Fracture": None}, "probability_type_invalid"),
        ({**_row(), "Fracture": True}, "probability_type_invalid"),
        ({**_row(), "Fracture": float("nan")}, "probability_nonfinite"),
        ({**_row(), "Fracture": float("inf")}, "probability_nonfinite"),
        ({**_row(), "Fracture": -0.0001}, "probability_out_of_range"),
        ({**_row(), "Fracture": 1.0001}, "probability_out_of_range"),
        ({label: 0.5 for label in LABELS[:-1]}, "probability_condition_missing"),
        ({**_row(), "unexpected": 0.5}, "probability_condition_extra"),
    ],
)
def test_writer_rejects_invalid_probability_values_and_conditions(
    tmp_path, template, values, code
):
    output = tmp_path / "submission.csv"
    rows = [(uid, values) for uid in _template_uids(template)]
    with pytest.raises(SubmissionError) as caught:
        write_submission(
            template,
            output,
            rows,
            source_provenance={"kind": "test"},
        )
    assert caught.value.code == code
    assert not output.exists()


def test_invalid_input_does_not_replace_existing_output(tmp_path, template):
    output = tmp_path / "submission.csv"
    output.write_text("previous contents\n", encoding="utf-8")
    rows = [(uid, _row()) for uid in _template_uids(template)]
    rows[-1] = (rows[-1][0], {**rows[-1][1], "ACL": float("nan")})

    with pytest.raises(SubmissionError, match="probability_nonfinite"):
        write_submission(
            template,
            output,
            rows,
            source_provenance={"kind": "test"},
        )

    assert output.read_text(encoding="utf-8") == "previous contents\n"


def test_validator_rejects_uid_order_and_malformed_csv(tmp_path, template):
    uids = _template_uids(template)
    reordered = tmp_path / "reordered.csv"
    with reordered.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.writer(stream)
        writer.writerow(SUBMISSION_COLUMNS)
        for uid in reversed(uids):
            writer.writerow((uid, *(["0.5"] * len(LABELS))))
    with pytest.raises(SubmissionError) as caught:
        validate_submission(template, reordered)
    assert caught.value.code == "submission_study_uid_order_mismatch"

    malformed = tmp_path / "malformed.csv"
    malformed.write_text("StudyInstanceUID,wrong\n", encoding="utf-8")
    with pytest.raises(SubmissionError) as caught:
        validate_submission(template, malformed)
    assert caught.value.code == "submission_columns_invalid"


@pytest.mark.parametrize(
    ("uids_to_write", "row_width", "expected_code"),
    [
        (
            lambda uids: uids[:-1],
            len(SUBMISSION_COLUMNS),
            "submission_study_uid_missing",
        ),
        (
            lambda uids: [*uids, "extra-study"],
            len(SUBMISSION_COLUMNS),
            "submission_study_uid_extra",
        ),
        (
            lambda uids: [*uids[:-1], uids[0]],
            len(SUBMISSION_COLUMNS),
            "submission_study_uid_duplicate",
        ),
        (
            lambda uids: uids,
            len(SUBMISSION_COLUMNS) - 1,
            "submission_condition_missing",
        ),
        (
            lambda uids: uids,
            len(SUBMISSION_COLUMNS) + 1,
            "submission_condition_extra",
        ),
    ],
)
def test_validator_names_missing_extra_duplicate_rows_and_conditions(
    tmp_path, template, uids_to_write, row_width, expected_code
):
    output = tmp_path / "candidate.csv"
    with output.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.writer(stream)
        writer.writerow(SUBMISSION_COLUMNS)
        for uid in uids_to_write(_template_uids(template)):
            writer.writerow([uid, *(["0.5"] * (row_width - 1))])

    with pytest.raises(SubmissionError) as caught:
        validate_submission(template, output)
    assert caught.value.code == expected_code


@pytest.mark.parametrize(
    ("value", "expected_code"),
    [
        ("", "submission_probability_invalid"),
        ("NaN", "submission_probability_nonfinite"),
        ("Infinity", "submission_probability_nonfinite"),
        ("-0.001", "submission_probability_out_of_range"),
        ("1.001", "submission_probability_out_of_range"),
    ],
)
def test_validator_rejects_invalid_candidate_probabilities(
    tmp_path, template, value, expected_code
):
    output = tmp_path / "candidate.csv"
    with output.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.writer(stream)
        writer.writerow(SUBMISSION_COLUMNS)
        for uid in _template_uids(template):
            writer.writerow((uid, value, *(["0.5"] * (len(LABELS) - 1))))
    with pytest.raises(SubmissionError) as caught:
        validate_submission(template, output)
    assert caught.value.code == expected_code


def test_writer_rejects_unsafe_provenance_and_template_target(tmp_path, template):
    uids = _template_uids(template)
    rows = [(uid, _row()) for uid in uids]
    with pytest.raises(SubmissionError) as caught:
        write_submission(
            template,
            template,
            rows,
            source_provenance={"not-finite": float("nan")},
        )
    assert caught.value.code == "submission_output_is_template"

    with pytest.raises(SubmissionError) as caught:
        write_submission(
            template,
            tmp_path / "submission.csv",
            rows,
            source_provenance={"not-finite": float("nan")},
        )
    assert caught.value.code == "source_provenance_not_json_safe"


def test_template_must_have_unique_nonempty_study_rows(tmp_path, template):
    empty = tmp_path / "empty-template.csv"
    empty.write_text(",".join(SUBMISSION_COLUMNS) + "\n", encoding="utf-8")
    with pytest.raises(SubmissionError) as caught:
        validate_submission(empty, template)
    assert caught.value.code == "template_has_no_studies"

    duplicate = tmp_path / "duplicate-template.csv"
    uid = _template_uids(template)[0]
    with duplicate.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.writer(stream)
        writer.writerow(SUBMISSION_COLUMNS)
        writer.writerow((uid, *(["0.5"] * len(LABELS))))
        writer.writerow((uid, *(["0.5"] * len(LABELS))))
    with pytest.raises(SubmissionError) as caught:
        validate_submission(duplicate, template)
    assert caught.value.code == "template_study_uid_duplicate"


def test_zero_and_one_are_valid_probabilities(tmp_path, template):
    uids = _template_uids(template)
    output = tmp_path / "boundaries.csv"
    rows = [(uid, _row(index % 2)) for index, uid in enumerate(uids)]

    write_submission(
        template,
        output,
        rows,
        source_provenance={"kind": "boundary-test"},
    )

    assert validate_submission(template, output)["study_count"] == len(uids)
