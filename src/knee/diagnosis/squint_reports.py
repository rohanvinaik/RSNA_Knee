"""Independent report-to-call exchange and source-enforced case admission.

Off-runtime tooling only: nothing here is imported by, or read during, inference.
Report text is read by a native/Claude human-level reader outside the pipeline.
The reader returns structured calls; this module checks that each call is bound
to the real report, then admits cheap, newly located, actual object profiles
as individual cases carrying those calls as their only teacher.

What is enforced from source rather than trusted:

* Exact twelve questions (``knee.study.tables.LABELS``), digit in -1/0/1 (bool
  and float refused), and a closed assertion vocabulary that must agree with
  the digit: present=+1, absent=-1, uncertain=0, not_mentioned=0.
* A signed or uncertain call must quote a sentence that is actually in the
  report (exact, or equal after collapsing whitespace). ``not_mentioned`` has no
  sentence and can never be -1: report silence is never a negative.
* The call carries ``report_sha`` and is refused unless it equals the SHA-256 of
  the report text supplied for that study.
* ``source`` must be a report source (``report:...``). Visual-memory, recall,
  squint, locator and prediction sources, and any prediction-shaped field, are
  refused: recall outputs are never a teacher.
* Scope is the study-level condition statement of the report. A report does not
  localize a condition to tissue or pixels and no admitted case claims it does.
* The same source+scope call is counted once (``duplicate``). Opposing signed
  calls are all retained and marked ``contradictory``; they are never averaged,
  resolved or admitted as signed teaching. Calls flagged ``needs_review`` are
  retained for a human and teach nothing.
* An abstention (digit 0) is retained in the receipt and adds no signed case,
  no trust record and no censor.

No text is classified here. The reader, not this module, decides what a report
says; the checks above only make the reader's call verifiable and attributable.
There is no diagnosis regex, keyword list over report words, or negative derived
from absence of a mention.

Admission never mutates the supplied memory. It returns a shallow-copied next
revision dict (shared read-only backing is kept) whose ``cases`` container is a
new object of the same kind. New cases follow the knee.squint-memory/v1 case
fields and keep the full-profile pairing only where the finding carries one;
otherwise ``full_profile`` is None and ``full_source`` honestly says it is
unavailable.
"""

from __future__ import annotations

import contextlib
import copy
import hashlib
import json
import math
import os
import tempfile
from collections.abc import Iterable, Mapping, Sequence
from numbers import Integral
from pathlib import Path
from typing import Any

from knee.diagnosis.declarations import QUESTIONS
from knee.study.tables import LABELS, TRAIN_COLUMNS, read_rows

CALL_SCHEMA = "knee.squint-report-call/v1"
CALLS_DOCUMENT_SCHEMA = "knee.squint-report-calls/v1"
BATCH_SCHEMA = "knee.squint-report-batch/v1"
ADMISSION_SCHEMA = "knee.squint-report-admission/v1"
CASE_IDENTITY_SCHEMA = "knee.squint-report-case/v1"
MEMORY_SCHEMA = "knee.squint-memory/v1"
PROFILE_SCHEMA = "knee.squint-profile/v1"

REPORT_SCOPES: tuple[str, ...] = ("study_condition",)
SOURCE_PREFIX = "report:"
ASSERTIONS: tuple[str, ...] = ("present", "absent", "uncertain", "not_mentioned")
ACCEPTED_STATUSES: tuple[str, ...] = ("signed", "abstention")
LOCATED_STATUSES: tuple[str, ...] = ("located",)

_REQUIRED_FIELDS: tuple[str, ...] = (
    "study_uid",
    "question",
    "digit",
    "assertion",
    "sentence",
    "subject",
    "scope",
    "source",
    "report_sha",
    "reader",
)
_OPTIONAL_FIELDS: tuple[str, ...] = ("schema", "note", "needs_review")
_TEXT_FIELDS: tuple[str, ...] = tuple(
    name for name in _REQUIRED_FIELDS if name not in ("digit", "sentence")
)

# Fields that would smuggle a recall/prediction output in as a teacher.
PREDICTION_FIELDS: frozenset[str] = frozenset(
    {
        "prediction",
        "predictions",
        "predicted",
        "predicted_label",
        "predicted_digit",
        "recall",
        "recall_outcome",
        "outcome",
        "verdict",
        "probability",
        "score",
        "nearest_cases",
        "case_terms",
        "speaking_calls",
    }
)
_PREDICTION_TOKENS: frozenset[str] = frozenset(
    {
        "predict",
        "predicted",
        "prediction",
        "predictions",
        "pred",
        "classifier",
        "vote",
        "outcome",
        "verdict",
        "probability",
    }
)
_VISUAL_MEMORY_TOKENS: frozenset[str] = frozenset(
    {
        "recall",
        "squint",
        "memory",
        "locator",
        "located",
        "profile",
        "cosine",
        "nearest",
        "inference",
        "infer",
        "visual",
        "image",
        "pixel",
    }
)
_FINDING_CALL_FIELDS: tuple[str, ...] = (
    "condition_calls",
    "calls",
    "outcome",
    "prediction",
    "predicted",
    "case_terms",
    "speaking_calls",
)

_DECLARED_OBJECTS: dict[str, tuple[str, ...]] = {
    question.question_id: question.objects for question in QUESTIONS
}


class ReportCallError(ValueError):
    """A named malformed argument or unreadable exchange document."""

    def __init__(self, reason: str):
        self.reason = reason
        super().__init__(reason)


# ---------------------------------------------------------------------------
# Pure decision helpers: each returns a named code.
# ---------------------------------------------------------------------------


def digit_status(digit: object) -> str:
    """Classify a ternary call digit; bool and float are never digits.

    post: __return__ in ('invalid_digit', 'positive', 'negative', 'abstention')
    """
    if type(digit) is not int or digit not in (-1, 0, 1):
        return "invalid_digit"
    if digit == 1:
        return "positive"
    if digit == -1:
        return "negative"
    return "abstention"


def assertion_digit_code(assertion: object, digit: object, has_sentence: object) -> str:
    """Whether the reader's stated assertion, digit and quoted sentence cohere.

    present<->+1 and absent<->-1, each needing a quoted sentence. uncertain is
    an abstention that needs the equivocal sentence. not_mentioned is an
    abstention with no sentence and is never a sign: silence is not a negative.
    """
    if not isinstance(assertion, str) or assertion not in ASSERTIONS:
        return "invalid_assertion"
    if digit_status(digit) == "invalid_digit":
        return "invalid_digit"
    if type(has_sentence) is not bool:
        return "invalid_sentence_state"
    if assertion == "not_mentioned":
        if digit != 0:
            return "silence_not_a_sign"
        return "sentence_with_silence" if has_sentence else "not_mentioned_abstention"
    if not has_sentence:
        return "sentence_required"
    expected = {"present": 1, "absent": -1, "uncertain": 0}[assertion]
    if digit != expected:
        return "assertion_digit_mismatch"
    return {
        "present": "present_signed",
        "absent": "absent_signed",
        "uncertain": "uncertain_abstention",
    }[assertion]


def _squash(text: str) -> str:
    return " ".join(text.split())


def sentence_status(sentence: object, report: object) -> str:
    """Whether the quoted sentence is actually in the report (case-sensitive).

    "verbatim" is an exact substring; "verbatim_whitespace" matches only after
    collapsing runs of whitespace, e.g. a sentence the report wraps across lines.
    """
    if not isinstance(sentence, str) or not any(c.isalnum() for c in sentence):
        return "sentence_empty"
    if not isinstance(report, str):
        return "report_missing"
    if sentence in report:
        return "verbatim"
    if _squash(sentence) in _squash(report):
        return "verbatim_whitespace"
    return "not_in_report"


def _is_text(value: object) -> bool:
    return isinstance(value, str) and bool(value.strip()) and "\0" not in value


def _tokens(value: str) -> frozenset[str]:
    return frozenset("".join(c if c.isalnum() else " " for c in value.lower()).split())


def source_independence_code(source: object, reader: object) -> str:
    """Whether a call's source and reader are independent of visual memory.

    The teacher must be a report source (``report:...``) read by a named reader.
    Recall, squint, locator, profile or prediction identities are refused. This is
    a declaration check; the binding to the real report is report_sha plus the
    verbatim sentence.
    """
    if not _is_text(source):
        return "source_missing"
    if not _is_text(reader):
        return "reader_missing"
    for value in (source, reader):
        tokens = _tokens(value)
        if tokens & _PREDICTION_TOKENS:
            return "predicted_label_source"
        if tokens & _VISUAL_MEMORY_TOKENS:
            return "visual_memory_source"
    if not source.startswith(SOURCE_PREFIX) or source == SOURCE_PREFIX:
        return "source_not_report"
    return "independent_report"


def scope_code(scope: object) -> str:
    """A report states a condition for the study; it localizes nothing."""
    if isinstance(scope, str) and scope in REPORT_SCOPES:
        return scope
    return "scope_not_study_condition"


def subject_code(question: object, subject: object) -> str:
    """Whether the named subject is the condition composite or a declared object."""
    if not isinstance(question, str) or question not in LABELS:
        return "unknown_question"
    if not _is_text(subject):
        return "subject_missing"
    if subject == f"diagnosis/{question}":
        return "question_composite"
    if subject in _DECLARED_OBJECTS[question]:
        return "declared_object"
    return "subject_not_implicated"


def group_digits_code(digits: Iterable[object]) -> str:
    """Combine independent calls on one subject+question+scope without averaging.

    Abstentions speak nothing. Opposing signs are a named contradiction, never a
    resolution.
    """
    values = list(digits)
    if any(digit_status(d) == "invalid_digit" for d in values):
        return "invalid_digit"
    positive = 1 in values
    negative = -1 in values
    if positive and negative:
        return "contradictory"
    if positive:
        return "positive"
    if negative:
        return "negative"
    return "abstention_only" if values else "silent"


def repeat_code(previous: object, digit: object) -> str:
    """One source repeating its own call: same digit is once, otherwise self-conflict."""
    if (
        digit_status(previous) == "invalid_digit"
        or digit_status(digit) == "invalid_digit"
    ):
        return "invalid_digit"
    return "duplicate" if previous == digit else "self_contradiction"


def revision_code(revision: object, parent: object) -> str:
    """The next revision must be named and different from its parent."""
    if not _is_text(revision):
        return "revision_invalid"
    if parent is not None and revision == parent:
        return "revision_not_new"
    return "new"


def admission_call_code(status: object, digit: object) -> str:
    """What a validated call may do at admission."""
    if status == "signed":
        state = digit_status(digit)
        if state == "positive":
            return "teach_positive"
        if state == "negative":
            return "teach_negative"
        return "invalid_digit"
    return {
        "abstention": "abstain_no_case",
        "duplicate": "duplicate_ignored",
        "contradictory": "hold_contradictory",
        "needs_review": "hold_review",
    }.get(status if isinstance(status, str) else "", "rejected")


def _counts_valid(counts: object) -> bool:
    if isinstance(counts, (str, bytes, Mapping)) or not isinstance(counts, Iterable):
        return False
    values = list(counts)
    return len(values) == 3 and all(
        isinstance(v, Integral) and not isinstance(v, bool) and v >= 0 for v in values
    )


def profile_status(profile: object, subject: object, study_uid: object) -> str:
    """Whether a finding's profile is an actual, speaking, cheap squint profile.

    Missing banks are absent, never measured middle. Declared source study or
    mode, when stated, must agree with the finding.
    """
    if not isinstance(profile, Mapping):
        return "profile_missing"
    schema = profile.get("schema", profile.get("schema_version"))
    if schema != PROFILE_SCHEMA:
        return "profile_schema_unsupported"
    if profile.get("subject") != subject:
        return "profile_subject_mismatch"
    source = profile.get("source")
    source_uids: list[object] = []
    if isinstance(source, Mapping):
        pending: list[object] = [source]
        while pending:
            item = pending.pop()
            if isinstance(item, Mapping):
                declared = item.get("study_uid")
                if declared not in (None, ""):
                    source_uids.append(declared)
                pending.extend(item.values())
            elif isinstance(item, (list, tuple)):
                pending.extend(item)
        if not source_uids or any(declared != study_uid for declared in source_uids):
            return "profile_study_mismatch"
        mode = source.get("mode")
        if mode not in (None, "") and mode != "cheap":
            return "profile_not_cheap"
    else:
        return "profile_study_mismatch"
    banks = profile.get("banks")
    if (
        not isinstance(banks, Mapping)
        or any(not _is_text(name) for name in banks)
        or not all(_counts_valid(counts) for counts in banks.values())
    ):
        return "profile_banks_invalid"
    if not any(int(c) for counts in banks.values() for c in counts):
        return "profile_silent"
    return "speaking"


def finding_admission_code(
    finding: object, located_statuses: Sequence[str] = LOCATED_STATUSES
) -> str:
    """Whether a finding is a located, actual, speaking cheap profile to teach."""
    if not isinstance(finding, Mapping):
        return "finding_not_mapping"
    study_uid = finding.get("study_uid")
    subject = finding.get("subject")
    if not _is_text(study_uid):
        return "study_uid_missing"
    if not _is_text(subject):
        return "subject_missing"
    if finding.get("status") not in tuple(located_statuses):
        return "not_located"
    mode = finding.get("mode")
    if mode not in (None, "") and mode != "cheap":
        return "profile_not_cheap"
    state = profile_status(finding.get("profile"), subject, study_uid)
    if state != "speaking":
        return state
    return "admissible"


def memory_question_code(
    table: Mapping[str, frozenset[str] | None] | None, question: str, subject: str
) -> str:
    """Whether the memory's own declared question table admits this subject."""
    if table is None:
        return "no_memory_table"
    if question not in table:
        return "question_not_in_memory"
    objects = table[question]
    if objects is None or subject == f"diagnosis/{question}" or subject in objects:
        return "applicable"
    return "subject_not_in_memory_question"


# ---------------------------------------------------------------------------
# Canonical identity.
# ---------------------------------------------------------------------------


def report_sha256(text: str) -> str:
    """SHA-256 hex digest of the report's UTF-8 text."""
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _plain(value: Any) -> Any:
    if value is None or isinstance(value, (bool, str)):
        return value
    if isinstance(value, Integral):
        return int(value)
    if isinstance(value, float):
        return value if math.isfinite(value) else repr(value)
    if isinstance(value, Mapping):
        return {str(key): _plain(item) for key, item in value.items()}
    if isinstance(value, (set, frozenset)):
        return sorted((_plain(item) for item in value), key=repr)
    if hasattr(value, "tolist"):
        return _plain(value.tolist())
    if isinstance(value, (list, tuple)):
        return [_plain(item) for item in value]
    return repr(value)


def _canonical(value: Any) -> bytes:
    try:
        return json.dumps(
            _plain(value),
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        ).encode("utf-8")
    except (TypeError, ValueError, UnicodeError) as error:
        raise ReportCallError("not_canonical_json") from error


def _digest(value: Any) -> str:
    return hashlib.sha256(_canonical(value)).hexdigest()


def _seal(entry: Mapping[str, Any]) -> str:
    """Consistency digest of a call record; position metadata is not content."""
    return _digest(
        {k: v for k, v in entry.items() if k not in ("record_sha256", "index")}
    )


# ---------------------------------------------------------------------------
# Validation of reader-authored calls.
# ---------------------------------------------------------------------------


def _reject(index: int, record: object, status: str, detail: str = "") -> dict:
    out = {
        "schema": CALL_SCHEMA,
        "index": index,
        "status": status,
        "detail": detail,
        "record": _plain(record),
    }
    out["record_sha256"] = _seal(out)
    return out


def _check_record(index: int, record: object, reports: Mapping[str, str]) -> dict:
    if not isinstance(record, Mapping):
        return _reject(index, record, "record_not_mapping")
    keys = set(record)
    smuggled = keys & PREDICTION_FIELDS
    if smuggled:
        return _reject(
            index,
            record,
            "predicted_label_teacher",
            ",".join(sorted(map(str, smuggled))),
        )
    unknown = keys - set(_REQUIRED_FIELDS) - set(_OPTIONAL_FIELDS)
    if unknown:
        return _reject(
            index, record, "unknown_field", ",".join(sorted(map(str, unknown)))
        )
    missing = [name for name in _REQUIRED_FIELDS if name not in record]
    if missing:
        return _reject(index, record, "missing_field", ",".join(missing))
    if record.get("schema", CALL_SCHEMA) != CALL_SCHEMA:
        return _reject(index, record, "call_schema_unsupported")
    note = record.get("note", "")
    review = record.get("needs_review", False)
    sentence = record["sentence"]
    if (
        not all(_is_text(record[name]) for name in _TEXT_FIELDS)
        or not isinstance(sentence, str)
        or "\0" in sentence
        or not isinstance(note, str)
        or type(review) is not bool
    ):
        return _reject(index, record, "field_invalid")

    study_uid = record["study_uid"]
    question = record["question"]
    subject = record["subject"]
    scope = record["scope"]
    digit = record["digit"]
    if question not in LABELS:
        return _reject(index, record, "unknown_question")
    scope_state = scope_code(scope)
    if scope_state != "study_condition":
        return _reject(index, record, scope_state)
    subject_state = subject_code(question, subject)
    if subject_state not in ("question_composite", "declared_object"):
        return _reject(index, record, subject_state)
    independence = source_independence_code(record["source"], record["reader"])
    if independence != "independent_report":
        return _reject(index, record, independence)
    report = reports.get(study_uid)
    if not isinstance(report, str):
        return _reject(index, record, "report_missing")
    if report_sha256(report) != record["report_sha"]:
        return _reject(index, record, "report_sha_mismatch")
    basis = assertion_digit_code(record["assertion"], digit, bool(sentence.strip()))
    if basis not in (
        "present_signed",
        "absent_signed",
        "uncertain_abstention",
        "not_mentioned_abstention",
    ):
        return _reject(index, record, basis)
    if sentence.strip():
        match = sentence_status(sentence, report)
        if match not in ("verbatim", "verbatim_whitespace"):
            return _reject(index, record, match)
    else:
        match = "none"
    if review:
        status = "needs_review"
    else:
        status = "signed" if digit != 0 else "abstention"
    content = {
        "schema": CALL_SCHEMA,
        "study_uid": study_uid,
        "question": question,
        "digit": digit,
        "assertion": record["assertion"],
        "sentence_sha256": (
            hashlib.sha256(sentence.encode("utf-8")).hexdigest()
            if sentence.strip()
            else None
        ),
        "subject": subject,
        "scope": scope,
        "source": record["source"],
        "report_sha": record["report_sha"],
        "reader": record["reader"],
    }
    return {
        "schema": CALL_SCHEMA,
        "index": index,
        "status": status,
        "detail": "",
        "study_uid": study_uid,
        "question": question,
        "digit": digit,
        "assertion": record["assertion"],
        "sentence": sentence,
        "sentence_sha256": content["sentence_sha256"],
        "sentence_match": match,
        "subject": subject,
        "subject_kind": subject_state,
        "scope": scope,
        "source": record["source"],
        "report_sha": record["report_sha"],
        "reader": record["reader"],
        "note": note,
        "needs_review": review,
        "call_id": "call-sha256:" + _digest(content),
        "duplicate_of": None,
    }


def _classify(entries: Sequence[Mapping[str, Any]]) -> list[tuple[str, str | None]]:
    """Duplicate and contradiction status for already verified call entries.

    One source+scope call is counted once; a source that changes its own call, or
    independent sources of opposite sign, are all retained as contradictory.
    """
    outcome: list[tuple[str, str | None]] = [
        ("signed" if entry["digit"] != 0 else "abstention", None) for entry in entries
    ]
    by_source: dict[tuple, list[int]] = {}
    for pos, entry in enumerate(entries):
        key = (
            entry["study_uid"],
            entry["subject"],
            entry["question"],
            entry["scope"],
            entry["source"],
        )
        by_source.setdefault(key, []).append(pos)
    for positions in by_source.values():
        head = entries[positions[0]]
        later = positions[1:]
        if any(
            repeat_code(head["digit"], entries[p]["digit"]) == "self_contradiction"
            for p in later
        ):
            for p in positions:
                outcome[p] = ("contradictory", None)
        else:
            for p in later:
                outcome[p] = ("duplicate", head["call_id"])
    by_scope: dict[tuple, list[int]] = {}
    for pos, entry in enumerate(entries):
        if outcome[pos][0] == "signed":
            key = (
                entry["study_uid"],
                entry["subject"],
                entry["question"],
                entry["scope"],
            )
            by_scope.setdefault(key, []).append(pos)
    for positions in by_scope.values():
        if group_digits_code(entries[p]["digit"] for p in positions) == "contradictory":
            for p in positions:
                outcome[p] = ("contradictory", None)
    return outcome


def validate_report_calls(records: list, reports: dict[str, str]) -> list:
    """Verify reader-authored report calls against the real reports.

    Returns one result dict per input record, in input order, never mutating the
    inputs. ``status`` is one of: ``signed`` / ``abstention`` (verified and
    countable), ``duplicate`` (same source+scope call, counted once),
    ``contradictory`` (opposing calls, all retained), ``needs_review`` (reader
    flagged, teaches nothing) or a named rejection such as ``not_in_report``,
    ``report_sha_mismatch``, ``silence_not_a_sign`` or ``predicted_label_teacher``.
    A rejected result retains the original record for human review.
    """
    if not isinstance(reports, Mapping):
        raise ReportCallError("reports_mapping_required")
    if isinstance(records, (str, bytes, Mapping)) or not isinstance(records, Sequence):
        raise ReportCallError("report_call_records_list_required")
    results = [_check_record(i, record, reports) for i, record in enumerate(records)]
    positions = [i for i, r in enumerate(results) if r["status"] in ACCEPTED_STATUSES]
    outcome = _classify([results[i] for i in positions])
    for i, (status, duplicate_of) in zip(positions, outcome, strict=True):
        results[i]["status"] = status
        results[i]["duplicate_of"] = duplicate_of
    for result in results:
        if "record_sha256" not in result:
            result["record_sha256"] = _seal(result)
    return results


# ---------------------------------------------------------------------------
# Exchange files.
# ---------------------------------------------------------------------------


def _write_atomic(path: Path, data: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=path.parent, prefix=path.name + ".", suffix=".tmp")
    try:
        with os.fdopen(fd, "wb") as handle:
            handle.write(data)
        os.replace(tmp, path)
    except BaseException:
        with contextlib.suppress(OSError):
            os.unlink(tmp)
        raise


def read_reports(train_csv: Path) -> dict[str, str]:
    """StudyInstanceUID -> full Report text from train.csv. Labels are not read out."""
    reports: dict[str, str] = {}
    for row in read_rows(Path(train_csv), TRAIN_COLUMNS):
        uid = row["StudyInstanceUID"]
        if uid in reports:
            raise ReportCallError("duplicate_study_uid_in_train_csv")
        reports[uid] = row["Report"]
    return reports


def export_report_batch(
    train_csv: Path, out: Path, study_uids: Sequence[str] | None = None
) -> dict:
    """Write the full report text for a reader to turn into calls.

    The batch holds each study's complete report and its SHA-256, the exact
    twelve questions, the digit/assertion legend, valid subjects per question and
    a call template. The train.csv labels are deliberately not exported: the
    reader's calls come from the report, not from labels. Studies with a blank
    report are listed as skipped, never turned into negatives.
    """
    train_csv = Path(train_csv)
    out = Path(out)
    reports = read_reports(train_csv)
    if study_uids is None:
        selected = list(reports)
    else:
        if isinstance(study_uids, (str, bytes)) or not isinstance(study_uids, Iterable):
            raise ReportCallError("study_uids_list_required")
        selected = list(study_uids)
        if any(not isinstance(uid, str) for uid in selected):
            raise ReportCallError("study_uid_invalid")
        if len(set(selected)) != len(selected):
            raise ReportCallError("duplicate_study_uid_requested")
        unknown = [uid for uid in selected if uid not in reports]
        if unknown:
            raise ReportCallError("study_uid_not_in_train_csv")
    studies: list[dict[str, str]] = []
    skipped: dict[str, str] = {}
    for uid in selected:
        report = reports[uid]
        if not report.strip():
            skipped[uid] = "report_blank"
            continue
        studies.append(
            {"study_uid": uid, "report_sha256": report_sha256(report), "report": report}
        )
    csv_sha = hashlib.sha256(train_csv.read_bytes()).hexdigest()
    document = {
        "schema": BATCH_SCHEMA,
        "train_csv": {"name": train_csv.name, "sha256": csv_sha},
        "purpose": (
            "Full report text for a native/Claude human-level reader. Return "
            f"{CALL_SCHEMA} records; labels are not included."
        ),
        "questions": list(LABELS),
        "digits": {
            "1": "assertion present: the report affirms the condition",
            "-1": "assertion absent: the report explicitly states it is absent/normal",
            "0": "uncertain (equivocal sentence quoted) or not_mentioned (no sentence)",
        },
        "rules": [
            "Quote the supporting sentence verbatim from the report.",
            "A condition the report does not mention is not_mentioned (digit 0), never -1.",
            "Equivocal wording is uncertain (digit 0), with the equivocal sentence quoted.",
            "The report states the condition for the study; it does not localize it.",
            "Set needs_review true on anything ambiguous; it will teach nothing.",
            "Do not copy any recalled, predicted or label-derived value.",
        ],
        "scopes": list(REPORT_SCOPES),
        "assertions": list(ASSERTIONS),
        "subjects_by_question": {
            question: [f"diagnosis/{question}", *_DECLARED_OBJECTS[question]]
            for question in LABELS
        },
        "call_record_template": {
            "schema": CALL_SCHEMA,
            "study_uid": "<StudyInstanceUID>",
            "question": "<one of questions>",
            "digit": "<1 | -1 | 0>",
            "assertion": "<present | absent | uncertain | not_mentioned>",
            "sentence": "<verbatim report sentence; empty only for not_mentioned>",
            "subject": "<a subject listed for that question>",
            "scope": REPORT_SCOPES[0],
            "source": f"{SOURCE_PREFIX}{train_csv.name}",
            "report_sha": "<report_sha256 of the study>",
            "reader": "<reader id>",
            "needs_review": False,
            "note": "",
        },
        "studies": studies,
    }
    data = (json.dumps(document, ensure_ascii=False, indent=2) + "\n").encode("utf-8")
    _write_atomic(out, data)
    return {
        "schema": BATCH_SCHEMA,
        "out": str(out),
        "batch_sha256": hashlib.sha256(data).hexdigest(),
        "train_csv_sha256": csv_sha,
        "study_count": len(studies),
        "study_uids": [study["study_uid"] for study in studies],
        "skipped": skipped,
        "questions": list(LABELS),
    }


def read_batch_reports(path: Path) -> dict[str, str]:
    """The reports a batch carries, each verified against its stated SHA-256."""
    try:
        document = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise ReportCallError("report_batch_unreadable_or_invalid") from error
    if not isinstance(document, dict) or document.get("schema") != BATCH_SCHEMA:
        raise ReportCallError("report_batch_schema_unsupported")
    studies = document.get("studies")
    if not isinstance(studies, list):
        raise ReportCallError("report_batch_studies_required")
    reports: dict[str, str] = {}
    for study in studies:
        if (
            not isinstance(study, dict)
            or not isinstance(study.get("study_uid"), str)
            or not isinstance(study.get("report"), str)
            or study.get("report_sha256") != report_sha256(study["report"])
            or study["study_uid"] in reports
        ):
            raise ReportCallError("report_batch_study_invalid")
        reports[study["study_uid"]] = study["report"]
    return reports


def _parse_calls(raw: str, suffix: str) -> list:
    try:
        if suffix == ".jsonl":
            return [json.loads(line) for line in raw.splitlines() if line.strip()]
        document = json.loads(raw)
    except json.JSONDecodeError as error:
        raise ReportCallError("report_calls_json_invalid") from error
    if isinstance(document, list):
        return document
    if isinstance(document, dict):
        if document.get("schema") != CALLS_DOCUMENT_SCHEMA:
            raise ReportCallError("report_calls_schema_unsupported")
        calls = document.get("calls")
        if isinstance(calls, list):
            return calls
    raise ReportCallError("report_calls_document_invalid")


def import_report_calls(path: Path, reports: dict) -> list:
    """Read a reader's call file (JSON list, calls document, or JSONL) and validate it."""
    path = Path(path)
    try:
        raw = path.read_text(encoding="utf-8")
    except (OSError, UnicodeError) as error:
        raise ReportCallError("report_calls_unreadable") from error
    return validate_report_calls(_parse_calls(raw, path.suffix.lower()), reports)


# ---------------------------------------------------------------------------
# Admission into the next memory revision.
# ---------------------------------------------------------------------------


def _field(item: Any, name: str) -> Any:
    try:
        return item[name]
    except (KeyError, TypeError, IndexError):
        return None


def _memory_question_table(
    memory: Mapping[str, Any],
) -> dict[str, frozenset[str] | None] | None:
    raw = memory.get("questions")
    if raw is None and isinstance(memory.get("metadata"), Mapping):
        raw = memory["metadata"].get("questions")

    def objects_of(value: object) -> frozenset[str] | None:
        if isinstance(value, Mapping):
            value = value.get("objects")
        if isinstance(value, (list, tuple, set, frozenset)) and all(
            isinstance(item, str) for item in value
        ):
            return frozenset(value)
        return None

    if isinstance(raw, Mapping):
        return {str(question): objects_of(value) for question, value in raw.items()}
    if isinstance(raw, (list, tuple)):
        table: dict[str, frozenset[str] | None] = {}
        for item in raw:
            if isinstance(item, str):
                table[item] = None
            elif isinstance(item, Mapping):
                question = item.get("question_id", item.get("question", item.get("id")))
                if isinstance(question, str):
                    table[question] = objects_of(item)
        return table
    return None


def _flatten_findings(findings: Sequence[Any]) -> list[dict[str, Any]]:
    flat: list[dict[str, Any]] = []
    for element in findings:
        if (
            isinstance(element, Mapping)
            and isinstance(element.get("objects"), Mapping)
            and "profile" not in element
        ):
            for subject, obj in element["objects"].items():
                if isinstance(obj, Mapping):
                    merged = dict(obj)
                    merged.setdefault("study_uid", element.get("study_uid"))
                    merged.setdefault("subject", subject)
                    flat.append({"finding": merged})
                else:
                    flat.append({"finding": obj, "subject": subject})
        else:
            flat.append({"finding": element})
    return flat


def _entry_shape_ok(entry: Mapping[str, Any]) -> bool:
    return (
        all(_is_text(entry.get(name)) for name in _TEXT_FIELDS)
        and digit_status(entry.get("digit")) != "invalid_digit"
        and entry.get("scope") in REPORT_SCOPES
        and entry.get("question") in LABELS
        and isinstance(entry.get("call_id"), str)
        and isinstance(entry.get("sentence"), str)
    )


def _revision_error(revision: object, parent: object) -> None:
    state = revision_code(revision, parent)
    if state != "new":
        raise ReportCallError(state)


def admit_report_cases(
    memory: dict,
    findings: list,
    report_calls: list,
    revision: str,
    *,
    reports: Mapping[str, str] | None = None,
    located_statuses: Sequence[str] = LOCATED_STATUSES,
) -> dict:
    """Return the next memory revision with newly report-taught cheap cases.

    ``findings`` are located objects (flat ``study_uid/subject/status/profile/
    regions`` dicts, or a locator result with an ``objects`` mapping). A finding
    is taught only when it is located, an actual speaking cheap squint profile of
    that study and subject. Its calls come only from validated independent report
    calls naming that exact study and subject; any call-like field the finding
    itself carries (a recall outcome, say) is ignored. Contradictions, duplicates,
    review flags and abstentions are retained in the receipt and teach nothing;
    no trust or censor record is created. The supplied memory is never mutated.
    """
    if not isinstance(memory, Mapping):
        raise ReportCallError("memory_mapping_required")
    schema = memory.get("schema")
    if schema is not None and schema != MEMORY_SCHEMA:
        raise ReportCallError("memory_schema_unsupported")
    cases = memory.get("cases")
    if isinstance(cases, (str, bytes)) or not isinstance(cases, (Mapping, Sequence)):
        raise ReportCallError("memory_cases_required")
    parent_revision = memory.get("revision")
    _revision_error(revision, parent_revision)
    for name, value in (("findings", findings), ("report_calls", report_calls)):
        if isinstance(value, (str, bytes, Mapping)) or not isinstance(value, Sequence):
            raise ReportCallError(f"{name}_list_required")
    if isinstance(located_statuses, (str, bytes)) or not all(
        isinstance(s, str) for s in located_statuses
    ):
        raise ReportCallError("located_statuses_invalid")
    located = tuple(located_statuses)
    if reports is None:
        raise ReportCallError("needs_reports")
    if not isinstance(reports, Mapping) or any(
        not isinstance(uid, str) or not isinstance(text, str)
        for uid, text in reports.items()
    ):
        raise ReportCallError("reports_mapping_required")

    existing = list(cases.values()) if isinstance(cases, Mapping) else list(cases)
    existing_ids = {_field(c, "case_id") for c in existing} - {None}
    existing_questions: dict[tuple[object, object], set[str]] = {}
    prior_entries: list[dict[str, Any]] = []
    for case in existing:
        ref = (_field(case, "study_uid"), _field(case, "subject"))
        calls = _field(case, "condition_calls")
        if isinstance(calls, Mapping):
            existing_questions.setdefault(ref, set()).update(
                question for question in calls if isinstance(question, str)
            )
        teaching = _field(case, "teaching")
        prior_calls = _field(teaching, "calls")
        if isinstance(prior_calls, Sequence) and not isinstance(
            prior_calls, (str, bytes)
        ):
            for call in prior_calls:
                if not isinstance(call, Mapping):
                    continue
                if (
                    isinstance(ref[0], str)
                    and isinstance(ref[1], str)
                    and isinstance(call.get("question"), str)
                    and type(call.get("digit")) is int
                    and call.get("digit") in (-1, 1)
                ):
                    prior_entries.append(
                        {
                            "study_uid": ref[0],
                            "subject": ref[1],
                            "question": call["question"],
                            "scope": call.get("scope", "study_condition"),
                            "source": call.get("source", ""),
                            "reader": call.get("reader", ""),
                            "digit": call["digit"],
                            "call_id": call.get("call_id", ""),
                            "prior_case_id": _field(case, "case_id"),
                        }
                    )
    parent_cases_sha = _digest(sorted(str(i) for i in existing_ids))
    table = _memory_question_table(memory)

    # -- calls: recover raw reader records and revalidate against supplied reports.
    retained: dict[str, list[dict]] = {
        "abstentions": [],
        "contradictory": [],
        "needs_review": [],
        "duplicates": [],
        "rejected": [],
    }
    bucket = {
        "abstention": "abstentions",
        "contradictory": "contradictory",
        "needs_review": "needs_review",
        "duplicate": "duplicates",
    }
    raw_calls: list[object] = []
    integrity_rejections: list[dict[str, Any] | None] = []
    for record in report_calls:
        if isinstance(record, Mapping) and isinstance(record.get("record"), Mapping):
            raw_calls.append(_plain(record["record"]))
            integrity_rejections.append(None)
        elif isinstance(record, Mapping) and "call_id" in record:
            if record.get("schema") != CALL_SCHEMA or record.get(
                "record_sha256"
            ) != _seal(record):
                raw_calls.append({})
                integrity_rejections.append(
                    {**_plain(record), "status": "record_integrity_failed"}
                )
            else:
                raw_calls.append(
                    {
                        key: _plain(record[key])
                        for key in (*_REQUIRED_FIELDS, *_OPTIONAL_FIELDS)
                        if key in record
                    }
                )
                integrity_rejections.append(None)
        elif isinstance(record, Mapping) and record.get("status") in ACCEPTED_STATUSES:
            raw_calls.append({})
            integrity_rejections.append(
                {**_plain(record), "status": "record_integrity_failed"}
            )
        else:
            raw_calls.append(_plain(record))
            integrity_rejections.append(None)
    verified = validate_report_calls(raw_calls, dict(reports))
    for index, forced in enumerate(integrity_rejections):
        if forced is not None:
            verified[index] = forced
    entries = [entry for entry in verified if entry.get("status") in ACCEPTED_STATUSES]
    for entry in verified:
        if entry.get("status") not in ACCEPTED_STATUSES:
            name = bucket.get(entry.get("status"), "rejected")
            retained[name].append(_plain(entry))
    # Compare each new call with immutable, previously admitted calls.  Only the
    # new record is reclassified; the prior case remains byte-for-byte unchanged.
    prior_opposition: list[dict[str, Any]] = []
    for entry in entries:
        opposing = [
            prior
            for prior in prior_entries
            if (prior["study_uid"], prior["subject"], prior["question"], prior["scope"])
            == (entry["study_uid"], entry["subject"], entry["question"], entry["scope"])
            and prior["digit"] == -entry["digit"]
        ]
        if opposing and entry.get("status") == "signed":
            entry["status"] = "contradictory"
            entry["duplicate_of"] = None
            entry["record_sha256"] = _seal(entry)
            for prior in opposing:
                prior_opposition.append(
                    {
                        "new_call_id": entry["call_id"],
                        "prior_case_id": prior["prior_case_id"],
                        "prior_call_id": prior["call_id"],
                        "study_uid": entry["study_uid"],
                        "subject": entry["subject"],
                        "question": entry["question"],
                        "prior_digit": prior["digit"],
                        "new_digit": entry["digit"],
                    }
                )
    # Reclassify newly verified calls together, preserving opposition against
    # the existing memory as a separate immutable receipt above.
    for entry, (status, duplicate_of) in zip(entries, _classify(entries), strict=True):
        if entry.get("status") == "contradictory":
            continue
        entry["status"] = status
        entry["duplicate_of"] = duplicate_of
        entry["record_sha256"] = _seal(entry)
    signed = [
        e
        for e in entries
        if admission_call_code(e["status"], e["digit"])
        in ("teach_positive", "teach_negative")
    ]
    for entry in entries:
        if entry["status"] in bucket:
            retained[bucket[entry["status"]]].append(entry)
    calls_by_ref: dict[tuple[str, str], list[dict]] = {}
    for entry in signed:
        calls_by_ref.setdefault((entry["study_uid"], entry["subject"]), []).append(
            entry
        )
    # Why a located finding has no signed teaching, so a human can see it.
    held_refs: dict[tuple[str, str], str] = {}
    for name, code in (
        ("contradictory", "calls_contradictory"),
        ("needs_review", "call_needs_review"),
        ("abstentions", "no_signed_call"),
    ):
        for held in retained[name]:
            uid, subject = held.get("study_uid"), held.get("subject")
            if isinstance(uid, str) and isinstance(subject, str):
                held_refs.setdefault((uid, subject), code)

    # -- findings: located, actual, speaking cheap profiles only.
    skipped: list[dict[str, Any]] = []
    ref_outcome: dict[tuple[str, str], str] = {}
    candidates: dict[tuple[str, str], list[Mapping[str, Any]]] = {}
    for item in _flatten_findings(findings):
        finding = item["finding"]
        code = finding_admission_code(finding, located)
        uid = finding.get("study_uid") if isinstance(finding, Mapping) else None
        subject = (
            finding.get("subject")
            if isinstance(finding, Mapping)
            else item.get("subject")
        )
        if code != "admissible":
            ref = (uid, subject)
            if (
                isinstance(uid, str)
                and isinstance(subject, str)
                and (ref in calls_by_ref or ref in held_refs)
            ):
                ref_outcome.setdefault(ref, code)
                skipped.append({"study_uid": uid, "subject": subject, "code": code})
            continue
        candidates.setdefault((uid, subject), []).append(finding)

    new_cases: list[dict[str, Any]] = []
    admitted: list[dict[str, Any]] = []
    held_calls: list[dict[str, Any]] = []
    findings_without_calls = 0
    for ref in sorted(candidates):
        uid, subject = ref
        found = candidates[ref]
        ref_calls = calls_by_ref.get(ref, [])
        if len(found) > 1:
            ref_outcome[ref] = "finding_ambiguous"
            skipped.append(
                {"study_uid": uid, "subject": subject, "code": "finding_ambiguous"}
            )
            continue
        if not ref_calls:
            if ref in held_refs:
                ref_outcome[ref] = held_refs[ref]
                skipped.append(
                    {"study_uid": uid, "subject": subject, "code": held_refs[ref]}
                )
            else:
                findings_without_calls += 1
            continue
        usable = []
        for entry in ref_calls:
            state = memory_question_code(table, entry["question"], entry["subject"])
            if state in ("applicable", "no_memory_table"):
                usable.append(entry)
            else:
                held_calls.append(
                    {
                        "call_id": entry["call_id"],
                        "study_uid": uid,
                        "subject": subject,
                        "question": entry["question"],
                        "digit": entry["digit"],
                        "code": state,
                    }
                )
        already_questions = existing_questions.get(ref, set())
        newly_covered = []
        for entry in usable:
            if entry["question"] in already_questions:
                held_calls.append(
                    {
                        "call_id": entry["call_id"],
                        "study_uid": uid,
                        "subject": subject,
                        "question": entry["question"],
                        "digit": entry["digit"],
                        "code": "already_in_memory_question",
                    }
                )
            else:
                newly_covered.append(entry)
        usable = newly_covered
        if not usable:
            ref_outcome[ref] = (
                "already_in_memory_question"
                if already_questions
                else "no_applicable_signed_call"
            )
            skipped.append(
                {
                    "study_uid": uid,
                    "subject": subject,
                    "code": ref_outcome[ref],
                }
            )
            continue
        finding = found[0]
        usable.sort(key=lambda e: (e["question"], e["source"], e["call_id"]))
        condition_calls = {e["question"]: e["digit"] for e in usable}
        call_ids = sorted(e["call_id"] for e in usable)
        profile = copy.deepcopy(finding["profile"])
        regions = copy.deepcopy(finding["regions"]) if "regions" in finding else {}
        full_profile = finding.get("full_profile")
        if full_profile is not None:
            full_profile = copy.deepcopy(full_profile)
            full_source = copy.deepcopy(
                finding.get("full_source") or {"status": "declared_without_source"}
            )
        else:
            full_source = {
                "status": "unavailable",
                "reason": "cheap_only_report_taught",
            }
        case_id = "case-sha256:" + _digest(
            {
                "schema": CASE_IDENTITY_SCHEMA,
                "revision": revision,
                "study_uid": uid,
                "subject": subject,
                "profile": profile,
                "condition_calls": condition_calls,
                "call_ids": call_ids,
            }
        )
        if case_id in existing_ids:
            ref_outcome[ref] = "already_in_memory"
            skipped.append(
                {"study_uid": uid, "subject": subject, "code": "already_in_memory"}
            )
            continue
        teaching_source = "report-calls-sha256:" + _digest(call_ids)
        case = {
            "case_id": case_id,
            "study_uid": uid,
            "subject": subject,
            "condition_calls": condition_calls,
            "condition_scopes": {e["question"]: e["scope"] for e in usable},
            "profile": profile,
            "profile_mode": "cheap",
            "regions": regions,
            "full_profile": full_profile,
            "full_source": full_source,
            "location": {
                "status": finding.get("status"),
                "kind": "actual_cheap_located",
            },
            "teaching_source": teaching_source,
            "teaching_revision": revision,
            "teaching": {
                "kind": "independent_report_calls",
                "revision": revision,
                "source_scope": "study_condition",
                "pixel_localization_confirmed": False,
                "calls": [
                    {
                        key: e[key]
                        for key in (
                            "call_id",
                            "question",
                            "digit",
                            "assertion",
                            "sentence",
                            "sentence_sha256",
                            "scope",
                            "source",
                            "reader",
                            "report_sha",
                        )
                    }
                    for e in usable
                ],
            },
        }
        new_cases.append(case)
        ref_outcome[ref] = "admitted"
        admitted.append(
            {
                "case_id": case_id,
                "study_uid": uid,
                "subject": subject,
                "condition_calls": dict(condition_calls),
                "call_ids": call_ids,
                "teaching_source": teaching_source,
                "full_profile_available": full_profile is not None,
                "finding_calls_ignored": sorted(
                    key for key in _FINDING_CALL_FIELDS if key in finding
                ),
            }
        )

    unmatched = [
        {
            "call_id": e["call_id"],
            "study_uid": e["study_uid"],
            "subject": e["subject"],
            "question": e["question"],
            "digit": e["digit"],
            "code": (
                "already_in_memory_question"
                if e["question"]
                in existing_questions.get((e["study_uid"], e["subject"]), set())
                else ref_outcome.get(
                    (e["study_uid"], e["subject"]), "no_located_finding"
                )
            ),
        }
        for e in signed
        if ref_outcome.get((e["study_uid"], e["subject"])) != "admitted"
    ]
    admitted_call_ids = {cid for item in admitted for cid in item["call_ids"]}
    source_identities = sorted(
        {
            (e["source"], e["reader"], e["report_sha"])
            for e in signed
            if e["call_id"] in admitted_call_ids
        }
    )

    # -- next revision: shallow copy keeps shared read-only backing.
    if isinstance(cases, Mapping):
        new_container: Any = {**dict(cases), **{c["case_id"]: c for c in new_cases}}
    elif isinstance(cases, tuple):
        new_container = (*cases, *new_cases)
    else:
        new_container = [*cases, *new_cases]
    all_ids = sorted({str(i) for i in existing_ids} | {c["case_id"] for c in new_cases})
    receipt = {
        "schema": ADMISSION_SCHEMA,
        "revision": revision,
        "parent_revision": parent_revision,
        "parent_cases_sha256": parent_cases_sha,
        "cases_sha256": _digest(all_ids),
        "added_case_count": len(new_cases),
        "admitted": admitted,
        "skipped_findings": skipped,
        "findings_without_calls": findings_without_calls,
        "unmatched_calls": unmatched,
        "held_calls": held_calls,
        "prior_opposition": prior_opposition,
        "retained_calls": retained,
        "source_identities": [
            {"source": s, "reader": r, "report_sha": h} for s, r, h in source_identities
        ],
        "trust_added": 0,
        "censors_added": 0,
        "pixel_localization_confirmed": False,
        "source_scope": "study_condition",
    }
    result = dict(memory)
    # The parent's runtime view, preparation and manifest digest describe only
    # the parent population; the child gets a new revision and new cases.
    parent_view = result.pop("view", None)
    result.pop("prepared_recall", None)
    result.pop("memory_manifest_sha256", None)
    if parent_view is not None:
        receipt["parent_view_provenance"] = copy.deepcopy(parent_view)
    result["cases"] = new_container
    result["revision"] = revision
    result["parent_revision"] = parent_revision
    result["report_admissions"] = [*memory.get("report_admissions", ()), receipt]
    return result


__all__ = [
    "ACCEPTED_STATUSES",
    "ASSERTIONS",
    "REPORT_SCOPES",
    "ReportCallError",
    "admission_call_code",
    "admit_report_cases",
    "assertion_digit_code",
    "digit_status",
    "export_report_batch",
    "finding_admission_code",
    "group_digits_code",
    "import_report_calls",
    "memory_question_code",
    "profile_status",
    "read_batch_reports",
    "read_reports",
    "repeat_code",
    "report_sha256",
    "revision_code",
    "scope_code",
    "sentence_status",
    "source_independence_code",
    "subject_code",
    "validate_report_calls",
]
