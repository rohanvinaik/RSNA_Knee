"""Classify reviewed object presentations from complete study-level labels."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any

from knee.diagnosis.squint_identity import identity_condition_views
from knee.diagnosis.squint_locator import _scoped_cases
from knee.diagnosis.squint_memory import IMPLICATED_OBJECTS
from knee.objects.assignments import OBJECT_CODES
from knee.study.tables import LABELS

CORPUS_SCHEMA = "knee.squint-reviewed-object-buckets/v1"


def _implicated_questions_for_subject(subject: object) -> tuple[str, ...]:
    if not isinstance(subject, str):
        return ()
    if subject == "meniscus":
        medial = set(IMPLICATED_OBJECTS.get("medial_meniscus", ()))
        lateral = set(IMPLICATED_OBJECTS.get("lateral_meniscus", ()))
        combined = medial | lateral
        return tuple(question for question in LABELS if question in combined)
    return IMPLICATED_OBJECTS.get(subject, ())


def _parse_label_values(
    labels: object,
) -> tuple[dict[str, int], list[str], list[str]]:
    if labels is None:
        return {}, list(LABELS), []
    if not isinstance(labels, Mapping):
        return {}, [], list(LABELS)
    values: dict[str, int] = {}
    unknown: list[str] = []
    invalid: list[str] = []
    for question in LABELS:
        value = labels.get(question)
        if question not in labels or value is None:
            unknown.append(question)
        elif type(value) is int and value in (0, 1):
            values[question] = value
        else:
            invalid.append(question)
    return values, unknown, invalid


def _label_state_status(
    labels: object,
    implicated_positive: Sequence[str],
    unknown: Sequence[str],
    invalid: Sequence[str],
) -> str:
    if invalid:
        return "invalid_labels"
    if implicated_positive:
        return "condition_presentation"
    if labels is None:
        return "unlabelled"
    if unknown:
        return "incomplete"
    return "normal"


def object_state_from_labels(subject: str, labels: object) -> dict[str, Any]:
    """Classify one known object using all 12 official study labels.

    A known positive condition that implicates the subject yields a
    ``condition_presentation`` at the existing study scope. With all labels
    present and no implicated positive, the object is ``normal`` even when an
    unrelated condition is positive. Missing data stays ``unlabelled`` or
    ``incomplete``; it never becomes a normal call.
    """
    implicated = _implicated_questions_for_subject(subject)
    base: dict[str, Any] = {
        "subject": subject,
        "implicated_questions": list(implicated),
        "implicated_positive": [],
        "implicated_unknown": [],
        "positive_questions": [],
        "unknown_questions": [],
        "invalid_questions": [],
    }
    code = OBJECT_CODES.get(subject) if isinstance(subject, str) else None
    if code is None or code <= OBJECT_CODES.get("air", 1):
        return {"status": "invalid_subject", **base}

    values, unknown, invalid = _parse_label_values(labels)
    positive = [question for question in LABELS if values.get(question) == 1]
    implicated_positive = [
        question for question in implicated if values.get(question) == 1
    ]
    implicated_unknown = [question for question in implicated if question in unknown]
    status = _label_state_status(labels, implicated_positive, unknown, invalid)

    return {
        "status": status,
        **base,
        "implicated_positive": implicated_positive,
        "implicated_unknown": implicated_unknown,
        "positive_questions": positive,
        "unknown_questions": unknown,
        "invalid_questions": invalid,
    }


def _non_string_sequence(value: object) -> Sequence[Any] | None:
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes)):
        return value
    return None


def _confirmed_scoped_record(
    original: object,
    scoped_case: object,
    *,
    confirmed_ids: set[Any],
    scope: Mapping[str, Any],
    labels_by_uid: Mapping[Any, Any],
) -> dict[str, Any] | None:
    if not isinstance(original, Mapping) or not isinstance(scoped_case, Mapping):
        return None
    case_id = original.get("case_id")
    if (
        not isinstance(case_id, str)
        or case_id not in confirmed_ids
        or case_id not in scope["views"]
    ):
        return None
    identity_views = scope["views"][case_id]
    if identity_views is not None and not identity_views:
        return None
    call_rows = scope["calls"].get(case_id, ())
    if len(call_rows) != 1 or call_rows[0].get("call") != "confirm":
        return None
    subject = original.get("subject")
    uid = original.get("study_uid")
    if (
        not isinstance(subject, str)
        or subject not in OBJECT_CODES
        or not isinstance(uid, str)
    ):
        return None
    state = object_state_from_labels(subject, labels_by_uid.get(uid))
    if state["status"] == "invalid_subject":
        return None
    view_list = (
        None
        if identity_views is None
        else [list(view) for view in sorted(identity_views)]
    )
    return {
        "case_id": case_id,
        "source_case_id": case_id,
        "study_uid": uid,
        "subject": subject,
        "state": state,
        "identity_views": view_list,
        "identity_call": call_rows[0],
        "case": scoped_case,
    }


def reviewed_object_buckets(
    memory: object,
    labels_by_uid: object,
    label_source: object,
) -> dict[str, Any]:
    """Return confirmed object cases, scoped profiles, and unchanged signed tables.

    Profiles are taken from ``_scoped_cases`` so only banks in the confirming
    identity call's views are exposed. The included case retains its original
    condition calls, localized/question scopes, and full-profile references.
    No profile or clinical call is synthesized.
    """
    if not isinstance(memory, Mapping):
        return {
            "schema": CORPUS_SCHEMA,
            "outcome": "invalid_input",
            "reason": "memory_must_be_object",
        }
    cases = _non_string_sequence(memory.get("cases"))
    if cases is None:
        return {
            "schema": CORPUS_SCHEMA,
            "outcome": "invalid_input",
            "reason": "memory_cases_required",
        }
    if not isinstance(labels_by_uid, Mapping):
        return {
            "schema": CORPUS_SCHEMA,
            "outcome": "invalid_input",
            "reason": "labels_by_uid_required",
        }

    scope = identity_condition_views(memory)
    if scope.get("outcome") != "scoped":
        return {
            "schema": CORPUS_SCHEMA,
            "outcome": "invalid_identity_scope",
            "reason": scope.get("reason", "identity_scope_unavailable"),
        }
    teaching = memory.get("object_identity_teaching")
    confirmed = _non_string_sequence(
        teaching.get("confirmed_case_ids") if isinstance(teaching, Mapping) else None
    )
    if confirmed is None:
        return {
            "schema": CORPUS_SCHEMA,
            "outcome": "invalid_identity_scope",
            "reason": "confirmed_case_ids_required",
        }
    confirmed_ids = set(confirmed)
    scoped_cases = _scoped_cases(cases, scope)
    if len(scoped_cases) != len(cases):
        return {
            "schema": CORPUS_SCHEMA,
            "outcome": "invalid_identity_scope",
            "reason": "scoped_case_alignment_invalid",
        }

    buckets: dict[str, dict[str, list[str]]] = {}
    condition_buckets: dict[str, dict[str, list[str]]] = {}
    records: list[dict[str, Any]] = []
    for original, scoped_case in zip(cases, scoped_cases, strict=True):
        record = _confirmed_scoped_record(
            original,
            scoped_case,
            confirmed_ids=confirmed_ids,
            scope=scope,
            labels_by_uid=labels_by_uid,
        )
        if record is None:
            continue
        case_id = record["case_id"]
        subject = record["subject"]
        state = record["state"]
        records.append(record)
        buckets.setdefault(subject, {}).setdefault(state["status"], []).append(case_id)
        for question in state["implicated_positive"]:
            condition_buckets.setdefault(subject, {}).setdefault(question, []).append(
                case_id
            )

    return {
        "schema": CORPUS_SCHEMA,
        "outcome": "classified",
        "memory_revision": memory.get("revision"),
        "label_source": label_source,
        "buckets": buckets,
        "condition_buckets": condition_buckets,
        "scoped_records": records,
        # Carry the existing signed record tables unchanged so downstream
        # training can retain its negative and alternative identity expertise.
        "object_identity_cases": memory.get("object_identity_cases"),
        "object_identity_teaching": memory.get("object_identity_teaching"),
    }
