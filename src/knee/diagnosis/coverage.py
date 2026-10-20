"""Scope-honest inventory of independently taught cases and declared object roles."""

from __future__ import annotations

from collections.abc import Sequence

from knee.diagnosis.models import Call, Case, Profile, Question, Snapshot


class CoverageError(ValueError):
    """A malformed memory or declaration cannot be indexed without guessing."""


_SCHEMA = "knee.diagnostic-coverage/v1"
_ROLE_NOTE = (
    "Question.objects declaration/reference only; not proof of measured presence "
    "or a taught normal/disease state."
)


def _text(value: object) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _sequence(value: object, error: str) -> Sequence:
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes)):
        raise CoverageError(error)
    return value


def _questions(
    questions: Sequence[Question],
) -> tuple[tuple[Question, ...], dict[str, Question]]:
    raw = _sequence(questions, "questions_sequence_required")
    by_id: dict[str, Question] = {}
    seen_subjects: set[str] = set()
    ordered: list[Question] = []
    for question in raw:
        if not isinstance(question, Question):
            raise CoverageError("invalid_question")
        if not _text(question.question_id):
            raise CoverageError("invalid_question_id")
        if not _text(question.subject):
            raise CoverageError("invalid_question_subject")
        if question.question_id in by_id:
            raise CoverageError(f"duplicate_question_id:{question.question_id}")
        if question.subject in seen_subjects:
            raise CoverageError(f"duplicate_question_subject:{question.subject}")
        if not isinstance(question.objects, tuple) or any(
            not _text(name) for name in question.objects
        ):
            raise CoverageError(f"invalid_question_objects:{question.question_id}")
        if len(set(question.objects)) != len(question.objects):
            raise CoverageError(f"duplicate_question_object:{question.question_id}")
        by_id[question.question_id] = question
        seen_subjects.add(question.subject)
        ordered.append(question)
    return tuple(ordered), by_id


def _catalogue(object_catalogue: Sequence[str]) -> tuple[str, ...]:
    raw = _sequence(object_catalogue, "object_catalogue_sequence_required")
    names: list[str] = []
    seen: set[str] = set()
    for name in raw:
        if not _text(name):
            raise CoverageError("invalid_object_name")
        if name in seen:
            raise CoverageError(f"duplicate_object_name:{name}")
        seen.add(name)
        names.append(name)
    return tuple(names)


def _new_buckets() -> dict:
    return {
        "positive_case_ids": set(),
        "negative_case_ids": set(),
        "silent_case_ids": set(),
        "study_uids": set(),
        "source_scopes": {},
    }


def _add_case(
    bucket: dict,
    case: Case,
    *,
    digit: int,
    call_source: str | None,
) -> None:
    if digit == 1:
        bucket["positive_case_ids"].add(case.case_id)
    elif digit == -1:
        bucket["negative_case_ids"].add(case.case_id)
    else:
        bucket["silent_case_ids"].add(case.case_id)
    bucket["study_uids"].add(case.study_uid)
    bucket["source_scopes"][case.case_id] = {
        "case_id": case.case_id,
        "study_uid": case.study_uid,
        "profile_scope": case.profile.scope,
        "profile_source_id": case.profile.source_id,
        "call_source": call_source,
    }


def _bucket_record(question_id: str, subject: str, bucket: dict) -> dict:
    return {
        "question_id": question_id,
        "profile_subject": subject,
        "positive_case_ids": sorted(bucket["positive_case_ids"]),
        "negative_case_ids": sorted(bucket["negative_case_ids"]),
        "silent_case_ids": sorted(bucket["silent_case_ids"]),
        "study_uids": sorted(bucket["study_uids"]),
        "source_scopes": [
            bucket["source_scopes"][case_id]
            for case_id in sorted(bucket["source_scopes"])
        ],
    }


def _direct_call_record(question_id: str, bucket: dict) -> dict:
    record = _bucket_record(question_id, "", bucket)
    record.pop("profile_subject")
    return record


def _association_decision(
    profile_subject: str,
    calls: list[dict],
    question_subjects: dict[str, str],
) -> dict:
    """Return exact question links from primitive case data (#coverage scope pin)."""
    if not isinstance(profile_subject, str) or not profile_subject.strip():
        return {"code": "invalid_profile_subject", "associations": []}
    if not isinstance(calls, list):
        return {"code": "invalid_case_calls", "associations": []}
    if not isinstance(question_subjects, dict) or any(
        not isinstance(question_id, str)
        or not question_id.strip()
        or not isinstance(subject, str)
        or not subject.strip()
        for question_id, subject in question_subjects.items()
    ):
        return {"code": "invalid_question_subject_map", "associations": []}

    associations = []
    seen_questions: set[str] = set()
    for call in calls:
        if not isinstance(call, dict):
            return {"code": "invalid_case_call", "associations": []}
        question_id = call.get("question_id")
        digit = call.get("digit")
        source = call.get("source")
        if not isinstance(question_id, str) or not question_id.strip():
            return {"code": "invalid_call_question", "associations": []}
        if question_id not in question_subjects:
            return {
                "code": "unknown_question",
                "question_id": question_id,
                "associations": [],
            }
        if question_id in seen_questions:
            return {
                "code": "duplicate_case_question_call",
                "question_id": question_id,
                "associations": [],
            }
        seen_questions.add(question_id)
        if type(digit) is not int or digit not in (-1, 0, 1):
            return {
                "code": "invalid_call_digit",
                "question_id": question_id,
                "associations": [],
            }
        if not isinstance(source, str) or not source.strip():
            return {
                "code": "invalid_call_source",
                "question_id": question_id,
                "associations": [],
            }
        associations.append(
            {
                "question_id": question_id,
                "digit": digit,
                "call_source": source,
            }
        )

    if associations:
        return {"code": "associated", "associations": associations}

    question_id = next(
        (
            name
            for name, subject in question_subjects.items()
            if subject == profile_subject
        ),
        None,
    )
    if question_id is not None:
        return {
            "code": "associated",
            "associations": [
                {"question_id": question_id, "digit": 0, "call_source": None}
            ],
        }
    if profile_subject.startswith("diagnosis/"):
        return {
            "code": "unknown_question_subject",
            "profile_subject": profile_subject,
            "associations": [],
        }
    return {"code": "unassociated", "associations": []}


def _validated_case(
    case: object,
    seen_case_ids: set[str],
    questions_by_id: dict[str, Question],
) -> tuple[Case, tuple[tuple[Question, int, str | None], ...], bool]:
    if not isinstance(case, Case):
        raise CoverageError("invalid_case")
    if not _text(case.case_id):
        raise CoverageError("invalid_case_id")
    if case.case_id in seen_case_ids:
        raise CoverageError(f"duplicate_case_id:{case.case_id}")
    seen_case_ids.add(case.case_id)
    if not _text(case.study_uid):
        raise CoverageError(f"invalid_case_study_uid:{case.case_id}")
    if not isinstance(case.profile, Profile):
        raise CoverageError(f"invalid_case_profile:{case.case_id}")
    if not _text(case.profile.subject):
        raise CoverageError(f"invalid_profile_subject:{case.case_id}")
    if not _text(case.profile.scope):
        raise CoverageError(f"invalid_profile_scope:{case.case_id}")
    if not _text(case.profile.source_id):
        raise CoverageError(f"invalid_profile_source_id:{case.case_id}")
    if not isinstance(case.calls, tuple):
        raise CoverageError(f"invalid_case_calls:{case.case_id}")
    if any(not isinstance(call, Call) for call in case.calls):
        raise CoverageError(f"invalid_case_call:{case.case_id}")

    raw_calls = [
        {"question_id": call.question, "digit": call.digit, "source": call.source}
        for call in case.calls
    ]
    decision = _association_decision(
        case.profile.subject,
        raw_calls,
        {
            question_id: question.subject
            for question_id, question in questions_by_id.items()
        },
    )
    code = decision["code"]
    if code != "associated" and code != "unassociated":
        detail = decision.get("question_id", decision.get("profile_subject", ""))
        raise CoverageError(f"{code}:{case.case_id}:{detail}")
    associations = tuple(
        (
            questions_by_id[item["question_id"]],
            item["digit"],
            item["call_source"],
        )
        for item in decision["associations"]
    )
    return case, associations, code == "unassociated"


def coverage_for_snapshot(
    snapshot: Snapshot,
    questions: Sequence[Question],
    object_catalogue: Sequence[str],
) -> dict:
    """Index case coverage without broadening any call beyond its actual subject."""
    if not isinstance(snapshot, Snapshot):
        raise CoverageError("snapshot_required")
    if not _text(snapshot.revision):
        raise CoverageError("invalid_memory_revision")
    if not isinstance(snapshot.cases, tuple):
        raise CoverageError("snapshot_cases_sequence_required")

    ordered_questions, questions_by_id = _questions(questions)
    objects = _catalogue(object_catalogue)
    object_names = set(objects)
    for question in ordered_questions:
        for object_name in question.objects:
            if object_name not in object_names:
                raise CoverageError(
                    f"question_object_not_in_catalogue:{question.question_id}:{object_name}"
                )
    question_buckets: dict[tuple[str, str], dict] = {}
    role_cases: dict[str, set[str]] = {name: set() for name in objects}
    direct_buckets: dict[tuple[str, str], dict] = {}
    unassociated_case_ids: list[str] = []
    seen_case_ids: set[str] = set()

    for raw_case in snapshot.cases:
        case, associations, unassociated = _validated_case(
            raw_case, seen_case_ids, questions_by_id
        )
        if unassociated:
            unassociated_case_ids.append(case.case_id)
            continue
        for question, digit, call_source in associations:
            subject = case.profile.subject
            key = (question.question_id, subject)
            bucket = question_buckets.setdefault(key, _new_buckets())
            _add_case(bucket, case, digit=digit, call_source=call_source)

            for object_name in question.objects:
                if object_name in role_cases:
                    role_cases[object_name].add(case.case_id)

            if subject in role_cases:
                direct_buckets[(question.question_id, subject)] = bucket

    question_subjects = [
        _bucket_record(question_id, subject, bucket)
        for (question_id, subject), bucket in sorted(question_buckets.items())
    ]
    objects_output = []
    for object_name in objects:
        direct = [
            _direct_call_record(question_id, bucket)
            for (question_id, subject), bucket in sorted(direct_buckets.items())
            if subject == object_name
        ]
        declared_case_ids = sorted(role_cases[object_name])
        if direct:
            state = "direct_calls_present"
        elif declared_case_ids:
            state = "declared_role_only"
        else:
            state = "no_precedent"
        objects_output.append(
            {
                "object": object_name,
                "coverage_state": state,
                "direct_question_calls": direct,
                "declared_role_case_ids": declared_case_ids,
                "declared_role_reference": _ROLE_NOTE,
            }
        )

    return {
        "schema": _SCHEMA,
        "memory_revision": snapshot.revision,
        "question_subjects": question_subjects,
        "objects": objects_output,
        "unassociated_case_ids": sorted(unassociated_case_ids),
    }
