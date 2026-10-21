"""Assemble question-scoped combinations from individual squint cases.

The composed count banks retain their object roles. Official labels are copied
into a separate case call only after the label-independent profile is built.
"""

from __future__ import annotations

import json
from typing import Any

from knee.diagnosis.declarations import question_for
from knee.diagnosis.squint_interfaces import TERRITORY_PROCEDURE

_MEMORY_SCHEMA = "knee.squint-memory/v1"
_PROFILE_SCHEMA = "knee.squint-profile/v1"
_PROCEDURE = "knee.squint-profile/scan-tercile-v1"
#: Object-profile writers a configuration may compose. One configuration reads
#: one writer: object roles written by different procedures never share it.
_PROCEDURES = (_PROCEDURE, TERRITORY_PROCEDURE)
_CONFIGURATION_REVISION = "question-configurations-v1"


class ConfigurationProfileError(ValueError):
    """A named invalid question, object profile, or memory configuration."""

    def __init__(self, code: str):
        self.code = code
        super().__init__(code)


def _validate_profile(
    subject: str, value: dict[str, Any], procedure: str = _PROCEDURE
) -> dict[str, Any]:
    profile = value.get("profile") if "profile" in value else value
    if not isinstance(profile, dict) or profile.get("schema") != _PROFILE_SCHEMA:
        raise ConfigurationProfileError("object_profile_invalid")
    if profile.get("subject") != subject:
        raise ConfigurationProfileError("object_profile_subject_mismatch")
    profile_source = profile.get("source")
    if not isinstance(profile_source, dict):
        raise ConfigurationProfileError("object_profile_source_invalid")
    if profile_source.get("procedure") != procedure:
        raise ConfigurationProfileError("object_profile_procedure_mismatch")
    banks = profile.get("banks")
    if not isinstance(banks, dict):
        raise ConfigurationProfileError("object_profile_banks_invalid")
    for bank, counts in banks.items():
        if not isinstance(bank, str) or not bank:
            raise ConfigurationProfileError("object_profile_bank_name_invalid")
        if not isinstance(counts, (list, tuple)) or len(counts) != 3:
            raise ConfigurationProfileError("object_profile_bank_counts_invalid")
        if any(type(value) is not int or value < 0 for value in counts):
            raise ConfigurationProfileError("object_profile_bank_counts_invalid")
    return profile


def configuration_profile(
    profiles: dict[str, dict], question: str, *, procedure: str = _PROCEDURE
) -> dict:
    """Compose the exact declared object roles for one question.

    `profiles` maps canonical object subjects to either their memory case or a
    `knee.squint-profile/v1` profile. Missing roles stay explicit in the source
    record and contribute no banks. Non-question objects are not selected.
    `procedure` names the one writer whose object profiles are composed; every
    role must carry it, and the configuration is labelled with it.
    """
    if not isinstance(profiles, dict):
        raise ConfigurationProfileError("profiles_mapping_required")
    if not isinstance(question, str) or not question:
        raise ConfigurationProfileError("question_id_invalid")
    if procedure not in _PROCEDURES:
        raise ConfigurationProfileError("configuration_procedure_unknown")
    try:
        declaration = question_for(question)
    except KeyError as error:
        raise ConfigurationProfileError("question_id_unknown") from error

    banks: dict[str, list[int]] = {}
    role_sources: dict[str, dict[str, Any]] = {}
    missing_roles: list[dict[str, str]] = []
    for subject in declaration.objects:
        if subject not in profiles:
            missing_roles.append({"subject": subject, "status": "missing_object_case"})
            continue
        case_or_profile = profiles[subject]
        if case_or_profile is None:
            missing_roles.append(
                {"subject": subject, "status": "missing_object_profile"}
            )
            continue
        if not isinstance(case_or_profile, dict):
            raise ConfigurationProfileError("object_case_invalid")
        profile = _validate_profile(subject, case_or_profile, procedure)
        for bank_name, counts in profile["banks"].items():
            qualified = f"object/{subject}/{bank_name}"
            if qualified in banks:
                raise ConfigurationProfileError("qualified_bank_collision")
            banks[qualified] = list(counts)
        profile_source = profile["source"]
        role_sources[subject] = {
            "status": "present",
            "bank_count": len(profile["banks"]),
            "profile_source": profile_source,
            "full_profile": case_or_profile.get("full_profile"),
            "full_source": case_or_profile.get("full_source"),
        }

    return {
        "schema": _PROFILE_SCHEMA,
        "subject": declaration.subject,
        "banks": banks,
        "source": {
            "api": "knee.diagnosis.squint_configurations.configuration_profile/v1",
            "procedure": procedure,
            "question_id": declaration.question_id,
            "object_order": list(declaration.objects),
            "roles": role_sources,
            "missing_roles": missing_roles,
        },
    }


def with_configuration_cases(memory: dict, *, procedure: str = _PROCEDURE) -> dict:
    """Return a new memory with one label-backed case per available condition.

    Label values are stored only in each new case's `condition_calls` and
    `label_attribution`; they are never passed to or inserted into the profile
    composition function. `procedure` is the one object-profile writer the
    memory's cases were read with (see `configuration_profile`).
    """
    if not isinstance(memory, dict) or memory.get("schema") != _MEMORY_SCHEMA:
        raise ConfigurationProfileError("memory_schema_invalid")
    if procedure not in _PROCEDURES:
        raise ConfigurationProfileError("configuration_procedure_unknown")
    cases = memory.get("cases")
    ledger = memory.get("label_ledger")
    if not isinstance(cases, list) or not isinstance(ledger, dict):
        raise ConfigurationProfileError("memory_cases_or_label_ledger_invalid")

    cases_by_study: dict[str, dict[str, dict[str, Any]]] = {}
    case_ids: set[str] = set()
    object_subjects = {
        subject
        for declaration in _questions_in_order()
        for subject in declaration.objects
    }
    for case in cases:
        if not isinstance(case, dict):
            raise ConfigurationProfileError("memory_case_invalid")
        case_id = case.get("case_id")
        study_uid = case.get("study_uid")
        subject = case.get("subject")
        if (
            not isinstance(case_id, str)
            or not case_id
            or not isinstance(study_uid, str)
            or not study_uid
        ):
            raise ConfigurationProfileError("memory_case_identity_invalid")
        if case_id in case_ids:
            raise ConfigurationProfileError("memory_case_id_duplicate")
        case_ids.add(case_id)
        if isinstance(subject, str) and subject in object_subjects:
            by_subject = cases_by_study.setdefault(study_uid, {})
            if subject in by_subject:
                raise ConfigurationProfileError("study_object_case_duplicate")
            by_subject[subject] = case

    new_cases: list[dict[str, Any]] = []
    generated_by_id: dict[str, dict[str, Any]] = {}
    for study_uid, labels in ledger.items():
        if (
            not isinstance(study_uid, str)
            or not study_uid
            or not isinstance(labels, dict)
        ):
            raise ConfigurationProfileError("label_ledger_record_invalid")
        for declaration in _questions_in_order():
            value = labels.get(declaration.question_id)
            if value is None:
                continue
            if type(value) is not int or value not in (0, 1):
                raise ConfigurationProfileError("label_ledger_call_invalid")
            case_id = f"squint-configuration:{study_uid}:{declaration.question_id}"
            profile = configuration_profile(
                cases_by_study.get(study_uid, {}),
                declaration.question_id,
                procedure=procedure,
            )
            calls = {declaration.question_id: 1 if value == 1 else -1}
            generated = {
                "case_id": case_id,
                "study_uid": study_uid,
                "subject": declaration.subject,
                "condition_calls": calls,
                "presentation_scope": {
                    declaration.question_id: "study_condition_configuration"
                },
                "label_attribution": {
                    declaration.question_id: {
                        "source": "label_ledger",
                        "study_uid": study_uid,
                        "condition": declaration.question_id,
                    }
                },
                "profile": profile,
                "regions": [],
                "full_profiles": {
                    subject: case.get("full_profile")
                    for subject, case in cases_by_study.get(study_uid, {}).items()
                    if subject in declaration.objects
                },
                "full_sources": {
                    subject: case.get("full_source")
                    for subject, case in cases_by_study.get(study_uid, {}).items()
                    if subject in declaration.objects
                },
                "teaching_source": {
                    "kind": "official_train_csv_label_ledger",
                    "scope": "study_condition_configuration",
                },
            }
            generated_by_id[case_id] = generated

    for case_id, generated in generated_by_id.items():
        if case_id not in case_ids:
            new_cases.append(generated)
            continue
        existing = next(case for case in cases if case["case_id"] == case_id)
        if _canonical(existing) != _canonical(generated):
            raise ConfigurationProfileError("configuration_case_conflict")

    result = dict(memory)
    result["cases"] = [*cases, *new_cases]
    revision = memory.get("revision")
    if not isinstance(revision, str) or not revision:
        raise ConfigurationProfileError("memory_revision_invalid")
    suffix = f"+{_CONFIGURATION_REVISION}"
    result["revision"] = (
        revision if revision.endswith(suffix) else f"{revision}{suffix}"
    )
    return result


def _questions_in_order():
    from knee.diagnosis.declarations import QUESTIONS

    return QUESTIONS


def _canonical(value: dict[str, Any]) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
