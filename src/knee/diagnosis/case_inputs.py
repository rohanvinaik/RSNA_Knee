"""Import explicitly attributed calls against caller-supplied image profiles.

This module never turns a diagnosis label into an object call, and never
supplies trust or censor records. The input document only binds authored calls
to exact existing ``(study_uid, profile.subject)`` identities.
"""

from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

from knee.diagnosis.models import Call, Case, Profile, Snapshot
from knee.diagnosis.store import validate_case

_SCHEMA = "knee.diagnostic-case-inputs/v1"
_IDENTITY_SCHEMA = "knee.diagnostic-case-input-identity/v1"


class CaseInputError(ValueError):
    """A named malformed, ambiguous, or inconsistent case-input record."""

    def __init__(self, reason: str):
        self.reason = reason
        super().__init__(reason)


def call_profile_status(digit: object, profile_speaks: bool) -> str:
    """Classify an explicit ternary call against whether its profile speaks.

    post: __return__ in ('invalid_call_digit', 'invalid_profile_speaking_state',
        'abstention', 'signed_silent_profile', 'signed')
    """
    if type(profile_speaks) is not bool:
        return "invalid_profile_speaking_state"
    if type(digit) is not int or digit not in (-1, 0, 1):
        return "invalid_call_digit"
    if digit == 0:
        return "abstention"
    if not profile_speaks:
        return "signed_silent_profile"
    return "signed"


def _require_text(value: object, reason: str) -> str:
    if not isinstance(value, str) or not value.strip() or "\0" in value:
        raise CaseInputError(reason)
    return value


def _canonical(value: object) -> bytes:
    try:
        return json.dumps(
            value,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        ).encode("utf-8")
    except (TypeError, ValueError, UnicodeError) as error:
        raise CaseInputError("case_inputs_not_canonical_json") from error


def _read_document(source: Path | Mapping[str, object]) -> tuple[dict, str, str]:
    if isinstance(source, Path):
        try:
            raw = source.read_bytes()
            document = json.loads(raw)
        except (OSError, UnicodeError, json.JSONDecodeError) as error:
            raise CaseInputError(
                "case_inputs_document_unreadable_or_invalid"
            ) from error
        return document, hashlib.sha256(raw).hexdigest(), str(source.resolve())
    if not isinstance(source, Mapping):
        raise CaseInputError("case_inputs_document_required")
    document = dict(source)
    encoded = _canonical(document)
    return document, hashlib.sha256(encoded).hexdigest(), "in_memory_document"


def _profile_speaks(profile: Profile) -> bool:
    return any(any(rows) for rows in profile.bundle.counts)


def _metadata_study_uid(profile: Profile, requested_uid: str) -> None:
    declared: set[str] = set()
    for pairs in (profile.context, profile.provenance):
        for key, value in pairs:
            if key == "study_uid" and value:
                declared.add(value)
    if len(declared) > 1 or (declared and declared != {requested_uid}):
        raise CaseInputError("profile_study_uid_mismatch")


def _profile_identity(profile: Profile) -> str:
    """Fingerprint all profile identity fields plus exact sparse count rows."""
    banks = []
    for index, (bank, row) in enumerate(
        zip(profile.bundle.layout.banks, profile.bundle.counts, strict=True)
    ):
        nonzero = [
            [row_index, format(value, "x")]
            for row_index, value in enumerate(row)
            if value
        ]
        banks.append(
            {
                "index": index,
                "name": bank.name,
                "row_count": bank.row_count,
                "nonzero": nonzero,
            }
        )
    identity = {
        "schema": _IDENTITY_SCHEMA,
        "subject": profile.subject,
        "layout": {
            "layout_id": profile.bundle.layout.layout_id,
            "carrier_id": profile.bundle.layout.carrier_id,
            "banks": [
                [bank.name, bank.row_count] for bank in profile.bundle.layout.banks
            ],
        },
        "counts": banks,
        "mode": profile.mode,
        "scope": profile.scope,
        "source_id": profile.source_id,
        "context": sorted(profile.context),
        "bank_statuses": sorted(profile.bank_statuses),
        "provenance": sorted(profile.provenance),
    }
    return hashlib.sha256(_canonical(identity)).hexdigest()


def _resolve_profile(
    profiles_by_study: Mapping[str, Sequence[Profile]], study_uid: str, subject: str
) -> Profile:
    if study_uid not in profiles_by_study:
        raise CaseInputError("case_study_uid_not_found")
    study_profiles = profiles_by_study[study_uid]
    if not isinstance(study_profiles, Sequence) or isinstance(
        study_profiles, (str, bytes)
    ):
        raise CaseInputError("case_study_profiles_invalid")
    if any(not isinstance(profile, Profile) for profile in study_profiles):
        raise CaseInputError("case_study_profile_record_invalid")
    candidates = [profile for profile in study_profiles if profile.subject == subject]
    if not candidates:
        raise CaseInputError("case_profile_subject_not_found")
    if len(candidates) != 1:
        raise CaseInputError("case_profile_subject_ambiguous")
    return candidates[0]


def _calls(value: object, speaks: bool) -> tuple[Call, ...]:
    if not isinstance(value, list) or not value:
        raise CaseInputError("case_calls_required")
    calls: list[Call] = []
    seen: set[str] = set()
    for item in value:
        if not isinstance(item, dict) or set(item) - {
            "question",
            "digit",
            "source",
            "words",
        }:
            raise CaseInputError("case_call_record_invalid")
        question = _require_text(item.get("question"), "case_call_question_invalid")
        if question in seen:
            raise CaseInputError("case_call_question_duplicate")
        seen.add(question)
        digit = item.get("digit")
        state = call_profile_status(digit, speaks)
        if state == "invalid_call_digit":
            raise CaseInputError(state)
        if state == "signed_silent_profile":
            raise CaseInputError(state)
        source = _require_text(item.get("source"), "case_call_source_invalid")
        words = item.get("words", "")
        if not isinstance(words, str):
            raise CaseInputError("case_call_words_invalid")
        calls.append(Call(question, digit, source, words))
    return tuple(sorted(calls, key=lambda call: call.question))


def import_case_inputs(
    source: Path | Mapping[str, object],
    profiles_by_study: Mapping[str, Sequence[Profile]],
    *,
    revision: str,
) -> tuple[Snapshot, dict[str, Any]]:
    """Resolve explicit attributed calls to exact existing profiles.

    ``source`` is either a parsed ``knee.diagnostic-case-inputs/v1`` document
    or its JSON path. Every case record names one study UID and exact profile
    subject. Calls are authored inputs; this function does not derive calls,
    trust fractions, censors, or object combinations.
    """
    revision = _require_text(revision, "case_teaching_revision_invalid")
    if not isinstance(profiles_by_study, Mapping):
        raise CaseInputError("profiles_by_study_required")
    document, source_sha256, source_name = _read_document(source)
    if not isinstance(document, dict) or set(document) != {"schema", "cases"}:
        raise CaseInputError("case_inputs_document_shape_invalid")
    if document.get("schema") != _SCHEMA:
        raise CaseInputError("case_inputs_schema_unsupported")
    rows = document.get("cases")
    if not isinstance(rows, list):
        raise CaseInputError("case_inputs_cases_required")

    cases: list[Case] = []
    receipt_cases: list[dict[str, Any]] = []
    seen_references: set[tuple[str, str]] = set()
    seen_ids: set[str] = set()
    for row in rows:
        if not isinstance(row, dict) or set(row) != {"study_uid", "subject", "calls"}:
            raise CaseInputError("case_record_shape_invalid")
        study_uid = _require_text(row.get("study_uid"), "case_study_uid_invalid")
        subject = _require_text(row.get("subject"), "case_subject_invalid")
        reference = (study_uid, subject)
        if reference in seen_references:
            raise CaseInputError("case_profile_reference_duplicate")
        seen_references.add(reference)
        profile = _resolve_profile(profiles_by_study, study_uid, subject)

        provisional = Case("pending", study_uid, profile, (), revision)
        validation = validate_case(provisional)
        if validation != "valid":
            raise CaseInputError("case_profile_invalid:" + validation)
        _metadata_study_uid(profile, study_uid)
        calls = _calls(row.get("calls"), _profile_speaks(profile))
        provisional = Case("pending", study_uid, profile, calls, revision)
        validation = validate_case(provisional)
        if validation != "valid":
            raise CaseInputError("case_record_invalid:" + validation)
        profile_identity = _profile_identity(profile)
        call_identity = [
            {
                "question": call.question,
                "digit": call.digit,
                "source": call.source,
                "words": call.words,
            }
            for call in calls
        ]
        case_identity = {
            "schema": _IDENTITY_SCHEMA,
            "revision": revision,
            "study_uid": study_uid,
            "profile_identity": profile_identity,
            "calls": call_identity,
        }
        case_id = "case-sha256:" + hashlib.sha256(_canonical(case_identity)).hexdigest()
        if case_id in seen_ids:
            raise CaseInputError("case_identity_duplicate")
        seen_ids.add(case_id)
        case = Case(case_id, study_uid, profile, calls, revision)
        validation = validate_case(case)
        if validation != "valid":
            raise CaseInputError("case_record_invalid:" + validation)
        cases.append(case)
        receipt_cases.append(
            {
                "case_id": case_id,
                "study_uid": study_uid,
                "subject": subject,
                "profile_identity_sha256": profile_identity,
                "calls": call_identity,
            }
        )

    snapshot = Snapshot(revision, tuple(cases))
    receipt = {
        "schema": "knee.diagnostic-case-input-receipt/v1",
        "source_schema": _SCHEMA,
        "source": source_name,
        "source_sha256": source_sha256,
        "revision": revision,
        "case_count": len(cases),
        "trust_count": 0,
        "censor_count": 0,
        "cases": receipt_cases,
    }
    return snapshot, receipt


__all__ = ["CaseInputError", "call_profile_status", "import_case_inputs"]
