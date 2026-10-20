"""Write and validate the official competition submission CSV shape."""

from __future__ import annotations

import csv
import hashlib
import io
import json
import math
import os
import tempfile
from collections.abc import Mapping, Sequence
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any

from knee.study.tables import LABELS

SUBMISSION_SCHEMA = "knee.diagnostic-submission/v1"
SUBMISSION_COLUMNS = ("StudyInstanceUID", *LABELS)


class SubmissionError(ValueError):
    """A named refusal to write or accept a competition submission."""

    def __init__(self, code: str, detail: str = "") -> None:
        self.code = code
        self.detail = detail
        super().__init__(f"{code}:{detail}" if detail else code)


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _read_csv(
    path: Path, *, template: bool
) -> tuple[list[str], list[list[str]], bytes]:
    if not isinstance(path, Path):
        raise SubmissionError("csv_path_invalid")
    try:
        raw = path.read_bytes()
    except OSError as error:
        code = "template_unreadable" if template else "submission_unreadable"
        raise SubmissionError(code, str(path)) from error
    try:
        text = raw.decode("utf-8-sig")
        rows = list(csv.reader(io.StringIO(text, newline=""), strict=True))
    except (UnicodeDecodeError, csv.Error) as error:
        code = "template_csv_malformed" if template else "submission_csv_malformed"
        raise SubmissionError(code) from error
    if not rows or tuple(rows[0]) != SUBMISSION_COLUMNS:
        code = "template_columns_invalid" if template else "submission_columns_invalid"
        raise SubmissionError(code)
    return rows[0], rows[1:], raw


def _template_uids(template_path: Path) -> tuple[tuple[str, ...], bytes]:
    _, rows, raw = _read_csv(template_path, template=True)
    uids: list[str] = []
    seen: set[str] = set()
    for number, row in enumerate(rows, start=2):
        if len(row) != len(SUBMISSION_COLUMNS):
            raise SubmissionError("template_row_width_invalid", str(number))
        uid = row[0]
        if not uid.strip():
            raise SubmissionError("template_study_uid_empty", str(number))
        if uid in seen:
            raise SubmissionError("template_study_uid_duplicate", uid)
        seen.add(uid)
        uids.append(uid)
    if not uids:
        raise SubmissionError("template_has_no_studies")
    return tuple(uids), raw


def _decimal_probability(value: Any, uid: str, condition: str) -> str:
    if isinstance(value, bool) or not isinstance(value, (int, float, Decimal)):
        raise SubmissionError("probability_type_invalid", f"{uid}:{condition}")
    if isinstance(value, float) and not math.isfinite(value):
        raise SubmissionError("probability_nonfinite", f"{uid}:{condition}")
    try:
        number = value if isinstance(value, Decimal) else Decimal(str(value))
    except (InvalidOperation, ValueError) as error:
        raise SubmissionError("probability_invalid", f"{uid}:{condition}") from error
    if not number.is_finite():
        raise SubmissionError("probability_nonfinite", f"{uid}:{condition}")
    if number < 0 or number > 1:
        raise SubmissionError("probability_out_of_range", f"{uid}:{condition}")
    return format(number, "f")


def _validated_rows(
    template_uids: tuple[str, ...],
    probability_rows: Sequence[tuple[str, Mapping[str, Any]]],
) -> dict[str, tuple[str, ...]]:
    if isinstance(probability_rows, (str, bytes)) or not isinstance(
        probability_rows, Sequence
    ):
        raise SubmissionError("probability_rows_invalid")
    expected_uids = set(template_uids)
    rows: dict[str, tuple[str, ...]] = {}
    for item in probability_rows:
        if not isinstance(item, tuple) or len(item) != 2:
            raise SubmissionError("probability_row_invalid")
        uid, values = item
        if type(uid) is not str or not uid.strip():
            raise SubmissionError("probability_study_uid_invalid")
        if uid not in expected_uids:
            raise SubmissionError("probability_study_uid_extra", uid)
        if uid in rows:
            raise SubmissionError("probability_study_uid_duplicate", uid)
        if not isinstance(values, Mapping):
            raise SubmissionError("probability_conditions_invalid", uid)
        keys = tuple(values.keys())
        if any(type(key) is not str for key in keys):
            raise SubmissionError("probability_condition_name_invalid", uid)
        supplied = set(keys)
        expected = set(LABELS)
        if supplied != expected:
            missing = tuple(name for name in LABELS if name not in supplied)
            extra = tuple(name for name in keys if name not in expected)
            if missing:
                raise SubmissionError(
                    "probability_condition_missing", f"{uid}:{missing[0]}"
                )
            raise SubmissionError("probability_condition_extra", f"{uid}:{extra[0]}")
        rows[uid] = tuple(
            _decimal_probability(values[name], uid, name) for name in LABELS
        )
    missing_uids = tuple(uid for uid in template_uids if uid not in rows)
    if missing_uids:
        raise SubmissionError("probability_study_uid_missing", missing_uids[0])
    return rows


def _source_provenance(value: Mapping[str, Any]) -> dict[str, Any]:
    if not isinstance(value, Mapping):
        raise SubmissionError("source_provenance_invalid")
    copied = dict(value)
    if any(type(key) is not str for key in copied):
        raise SubmissionError("source_provenance_invalid")
    try:
        json.dumps(copied, sort_keys=True, allow_nan=False)
    except (TypeError, ValueError, OverflowError) as error:
        raise SubmissionError("source_provenance_not_json_safe") from error
    return copied


def validate_submission(template_path: Path, submission_path: Path) -> dict[str, Any]:
    """Validate exact template UID coverage/order and finite [0, 1] values."""
    template_uids, template_bytes = _template_uids(template_path)
    _, rows, submission_bytes = _read_csv(submission_path, template=False)
    submitted_uids: list[str] = []
    seen: set[str] = set()
    for number, row in enumerate(rows, start=2):
        if len(row) != len(SUBMISSION_COLUMNS):
            if len(row) < len(SUBMISSION_COLUMNS):
                condition_index = min(len(row) - 1, len(LABELS) - 1)
                condition = LABELS[max(0, condition_index)]
                raise SubmissionError(
                    "submission_condition_missing", f"line {number}:{condition}"
                )
            raise SubmissionError("submission_condition_extra", f"line {number}")
        uid = row[0]
        if not uid.strip():
            raise SubmissionError("submission_study_uid_empty", str(number))
        if uid in seen:
            raise SubmissionError("submission_study_uid_duplicate", uid)
        seen.add(uid)
        submitted_uids.append(uid)
        for condition, raw_value in zip(LABELS, row[1:], strict=True):
            try:
                value = Decimal(raw_value)
            except InvalidOperation as error:
                raise SubmissionError(
                    "submission_probability_invalid", f"{uid}:{condition}"
                ) from error
            if not value.is_finite():
                raise SubmissionError(
                    "submission_probability_nonfinite", f"{uid}:{condition}"
                )
            if value < 0 or value > 1:
                raise SubmissionError(
                    "submission_probability_out_of_range", f"{uid}:{condition}"
                )
    if tuple(submitted_uids) != template_uids:
        submitted_set = set(submitted_uids)
        template_set = set(template_uids)
        missing_uids = tuple(uid for uid in template_uids if uid not in submitted_set)
        if missing_uids:
            raise SubmissionError("submission_study_uid_missing", missing_uids[0])
        extra_uids = tuple(uid for uid in submitted_uids if uid not in template_set)
        if extra_uids:
            raise SubmissionError("submission_study_uid_extra", extra_uids[0])
        raise SubmissionError("submission_study_uid_order_mismatch")
    return {
        "schema": SUBMISSION_SCHEMA,
        "template_path": str(template_path.resolve()),
        "template_sha256": _sha256(template_bytes),
        "submission_path": str(submission_path.resolve()),
        "submission_sha256": _sha256(submission_bytes),
        "columns": list(SUBMISSION_COLUMNS),
        "study_count": len(template_uids),
    }


def write_submission(
    template_path: Path,
    output_path: Path,
    probability_rows: Sequence[tuple[str, Mapping[str, Any]]],
    *,
    source_provenance: Mapping[str, Any],
) -> dict[str, Any]:
    """Atomically write explicit probability rows in official template order.

    This function serializes probabilities already supplied by the caller. It does
    not convert ternary calls, cosine values or diagnostic evidence into scores.
    """
    if not isinstance(template_path, Path):
        raise SubmissionError("template_path_invalid")
    if not isinstance(output_path, Path):
        raise SubmissionError("submission_path_invalid")
    if template_path.resolve() == output_path.resolve():
        raise SubmissionError("submission_output_is_template")
    template_uids, template_bytes = _template_uids(template_path)
    values_by_uid = _validated_rows(template_uids, probability_rows)
    provenance = _source_provenance(source_provenance)
    parent = output_path.parent
    try:
        parent.mkdir(parents=True, exist_ok=True)
    except OSError as error:
        raise SubmissionError("submission_parent_unavailable", str(parent)) from error
    temp_path: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            newline="",
            dir=parent,
            prefix=f".{output_path.name}.",
            suffix=".tmp",
            delete=False,
        ) as stream:
            temp_path = Path(stream.name)
            writer = csv.writer(stream, lineterminator="\n")
            writer.writerow(SUBMISSION_COLUMNS)
            for uid in template_uids:
                writer.writerow((uid, *values_by_uid[uid]))
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temp_path, output_path)
        temp_path = None
        directory_fd = os.open(parent, os.O_RDONLY)
        try:
            os.fsync(directory_fd)
        finally:
            os.close(directory_fd)
    except (OSError, csv.Error) as error:
        raise SubmissionError("submission_write_failed", str(output_path)) from error
    finally:
        if temp_path is not None:
            try:
                temp_path.unlink()
            except FileNotFoundError:
                pass
    checked = validate_submission(template_path, output_path)
    return {
        **checked,
        "source_provenance": provenance,
        "template_sha256_before_write": _sha256(template_bytes),
    }
