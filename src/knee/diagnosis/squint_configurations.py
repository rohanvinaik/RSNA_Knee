"""Assemble question-scoped combinations from individual squint cases.

The composed count banks retain their object roles. Official labels are copied
into a separate case call only after the label-independent profile is built.

Any publication that adds warranted object cases to a study (a growth round's
admissions, a direct visual teaching publication) rebuilds that study's
whole-condition cases with ``rebuild_study_configurations`` and places them with
``apply_rebuilt_configurations``: the seed's own scoped builder, every role on the
views where its identity holds and with its own provenance, the same case ids,
and each replaced version recorded (CLASSICAL_AI_BUILD_DESIGN §§5.1, 11).
"""

from __future__ import annotations

import copy
import json
from collections.abc import Iterable, Mapping
from typing import Any

from knee.diagnosis.declarations import question_for
from knee.diagnosis.squint_interfaces import TERRITORY_PROCEDURE
from knee.diagnosis.squint_memory import _json_sha256, _link_configuration_full_profiles

_MEMORY_SCHEMA = "knee.squint-memory/v1"
_PROFILE_SCHEMA = "knee.squint-profile/v1"
_PROCEDURE = "knee.squint-profile/scan-tercile-v1"
#: Object-profile writers a configuration may compose. One configuration reads
#: one writer: object roles written by different procedures never share it.
_PROCEDURES = (_PROCEDURE, TERRITORY_PROCEDURE)
_CONFIGURATION_REVISION = "question-configurations-v1"
#: A rebuilt configuration case's own record: its label source, the publication
#: that built it, each role's provenance and the version it replaced.
CONFIGURATION_TEACHING_SCHEMA = "knee.squint-configuration-teaching/v1"
#: A role whose identity a seed's visual review call confirmed.
SEED_CALL_KIND = "seed_visual_call"


class ConfigurationProfileError(ValueError):
    """A named invalid question, object profile, or memory configuration."""

    def __init__(self, code: str, detail: str | None = None):
        self.code = code
        self.detail = detail
        super().__init__(code if detail is None else f"{code}: {detail}")


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


def _text(value: object) -> bool:
    return isinstance(value, str) and bool(value)


def _rebuild_inputs(memory: object) -> tuple[list, Mapping, Mapping, set[str]]:
    """The parts of a memory a rebuild reads: cases, identity teaching, ledger, ids."""
    if not isinstance(memory, Mapping) or memory.get("schema") != _MEMORY_SCHEMA:
        raise ConfigurationProfileError("memory_schema_invalid")
    if not _text(memory.get("revision")):
        raise ConfigurationProfileError("memory_revision_invalid")
    cases = memory.get("cases")
    if not isinstance(cases, list) or not all(
        isinstance(case, Mapping)
        and all(_text(case.get(key)) for key in ("case_id", "study_uid", "subject"))
        for case in cases
    ):
        raise ConfigurationProfileError("memory_cases_or_label_ledger_invalid")
    teaching = memory.get("object_identity_teaching")
    if not isinstance(teaching, Mapping):
        raise ConfigurationProfileError("object_identity_teaching_required")
    ledger = memory.get("label_ledger")
    if ledger is None:
        ledger = {}
    elif not isinstance(ledger, Mapping):
        raise ConfigurationProfileError("memory_cases_or_label_ledger_invalid")
    known = {case["case_id"] for case in cases}
    table = memory.get("object_identity_cases")
    records = table.get("cases") if isinstance(table, Mapping) else None
    for record in records if isinstance(records, list) else ():
        if isinstance(record, Mapping) and _text(record.get("case_id")):
            known.add(record["case_id"])
    return cases, teaching, ledger, known


def _role_identity(
    case: Mapping[str, Any], row: Mapping[str, Any], reader: object
) -> dict[str, Any]:
    """A role's own identity provenance, pinned by digests and never copied.

    A recognition-derived admission (``identity_growth``) by its lineage; a
    direct visual teaching case (``direct_visual_teaching``) by its confirm call
    and its publication's provenance; otherwise the seed's visual review call.
    """
    lineage = case.get("identity_growth")
    if isinstance(lineage, Mapping):
        return {
            "kind": lineage.get("kind"),
            "independent_confirmation": lineage.get("independent_confirmation"),
            "parent_manifest_sha256": lineage.get("parent_manifest_sha256"),
            "lineage_sha256": _json_sha256(lineage),
        }
    visual = case.get("direct_visual_teaching")
    if isinstance(visual, Mapping):
        return {
            "kind": visual.get("kind"),
            "reader": row.get("reader", visual.get("reader")),
            "call_sha256": _json_sha256(row),
            "provenance_sha256": _json_sha256(visual),
        }
    return {
        "kind": SEED_CALL_KIND,
        "reader": row.get("reader", reader),
        "call_sha256": _json_sha256(row),
    }


def _role_links(staged: Mapping[str, Any]) -> dict[str, dict[str, Any]]:
    """Each role's link to its object case, its identity views and its provenance.

    ``identity_views`` are the views the role was composed on, its confirm
    call's as ``identity_condition_views`` reads them (None: a whole-case
    confirm, every view).
    """
    from knee.diagnosis.squint_identity import identity_condition_views

    scope = identity_condition_views(staged)
    if scope.get("outcome") != "scoped":
        raise ConfigurationProfileError(
            "configuration_identity_teaching_invalid", str(scope.get("reason"))
        )
    reader = staged["object_identity_teaching"].get("reader")
    links: dict[str, dict[str, Any]] = {}
    for case in staged["cases"]:
        case_id = case["case_id"]
        if case_id not in scope["views"]:
            raise ConfigurationProfileError("configuration_role_unconfirmed", case_id)
        views = scope["views"][case_id]
        [row] = scope["calls"][case_id]
        links[case["subject"]] = {
            "case_id": case_id,
            "identity_views": None
            if views is None
            else [list(view) for view in sorted(views)],
            "identity": _role_identity(case, row, reader),
        }
    return links


def _superseded(prior: Mapping[str, Any]) -> dict[str, Any]:
    """The version a rebuilt case replaces: its digest and who built it.

    ``built_by`` is that version's own record, or None when it carries none (the
    teaching set's publication built it).
    """
    teaching = prior.get("configuration_teaching")
    built_by = teaching.get("built_by") if isinstance(teaching, Mapping) else None
    return {"case_sha256": _json_sha256(prior), "built_by": copy.deepcopy(built_by)}


def _configuration_row(
    study: str,
    given: Mapping[str, int | None] | None,
    kept: Mapping[str, int | None] | None,
    configured: bool,
    label_source: Mapping[str, Any] | None,
) -> tuple[Mapping[str, int | None], dict[str, Any]] | None:
    """The official row a study's configurations are built from, and its source.

    The supplied row (``given``), named by ``label_source``; else the memory's
    ledger row (``kept``). None: the study has no row and no configuration
    case, so none is built. A supplied row differing from the ledger's
    (``label_ledger_row_conflict``) and a configured study with no row
    (``configuration_label_row_missing``) are refused.
    """
    if given is not None and kept is not None and dict(kept) != dict(given):
        raise ConfigurationProfileError("label_ledger_row_conflict", study)
    if given is not None:
        return given, {**(label_source or {}), "study_uid": study}
    if kept is not None:
        return kept, {"source": "label_ledger", "study_uid": study}
    if configured:
        raise ConfigurationProfileError("configuration_label_row_missing", study)
    return None


def rebuild_study_configurations(
    memory: Mapping[str, Any],
    study_uids: Iterable[str],
    *,
    built_by: Mapping[str, Any],
    labels: Mapping[str, Mapping[str, int | None]] | None = None,
    label_source: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Rebuild the whole-condition cases of studies whose warranted objects changed.

    ``memory`` already holds the new object cases and their confirm calls (a
    growth round's admissions, a direct visual publication's cases);
    ``study_uids`` names the studies whose object set changed. For each, the
    seed's own scoped builder (``squint_bootstrap._rebuilt_configurations``)
    composes one case per labelled question from every object case of that study
    in ``memory``, each role on the views where its identity holds in the
    memory's ``object_identity_teaching``, with missing roles explicit. Negative
    and alternative identity records are never roles. The call is the official
    label alone, at ``study_condition_configuration`` scope, and no case is made
    for a blank label; labels never enter the composition. The row is
    ``labels[study]`` (named by ``label_source``, which is then required), else
    the memory's ``label_ledger`` row (``_configuration_row``).

    Beside the builder's fields each case keeps ``configuration_teaching``: its
    label source, ``built_by`` (the caller's record of this publication, with a
    ``kind``), each role's case id, identity views and own provenance
    (``_role_identity``), and ``supersedes``. A case whose id the memory already
    holds for that study keeps the id and records the replaced version
    (``_superseded``); a held case the rebuild does not write
    (``configuration_rebuild_incomplete``) and a new id held outside that study
    (``configuration_case_conflict``) are refused, so one case per study and
    condition is ever live. A role's full profile is linked on the new cases.

    ``memory`` is never mutated. Returns ``study_uids`` rebuilt, every rebuilt
    ``cases`` in order, the ``new`` ones, the ``replaces`` by id, the replaced
    versions' digests (``superseded``) and the supplied rows the ``label_ledger``
    gains. ``apply_rebuilt_configurations`` places them. A named refusal raises
    ``ConfigurationProfileError`` with the study or case as its ``detail``.
    """
    from knee.diagnosis.squint_bootstrap import (
        SquintBootstrapError,
        _rebuilt_configurations,
    )

    cases, teaching, ledger, known = _rebuild_inputs(memory)
    if isinstance(study_uids, (str, bytes, Mapping)) or not isinstance(
        study_uids, Iterable
    ):
        raise ConfigurationProfileError("study_uids_invalid")
    studies = list(study_uids)
    if not all(_text(study) for study in studies):
        raise ConfigurationProfileError("study_uids_invalid")
    if not isinstance(built_by, Mapping) or not _text(built_by.get("kind")):
        raise ConfigurationProfileError("built_by_invalid")
    if labels is not None and (
        not isinstance(labels, Mapping) or not isinstance(label_source, Mapping)
    ):
        raise ConfigurationProfileError("labels_or_label_source_invalid")
    given = {} if labels is None else labels
    objects: dict[str, list[Mapping[str, Any]]] = {}
    held: dict[str, dict[str, Mapping[str, Any]]] = {}
    for case in cases:
        if case["subject"].startswith("diagnosis/"):
            held.setdefault(case["study_uid"], {})[case["case_id"]] = case
        else:
            objects.setdefault(case["study_uid"], []).append(case)
    # The teaching is indexed once; each study is scoped by its own cases' rows,
    # the same views the whole block gives them, without rereading every call.
    calls_by_id: dict[str, list[Mapping[str, Any]]] = {}
    for call in teaching.get("calls") or ():
        if isinstance(call, Mapping) and _text(call.get("candidate_id")):
            calls_by_id.setdefault(call["candidate_id"], []).append(call)
    confirmed = set(teaching.get("confirmed_case_ids") or ())
    result: dict[str, Any] = {
        "study_uids": [],
        "cases": [],
        "new": [],
        "replaces": {},
        "superseded": {},
        "label_ledger": {},
    }
    for study in sorted(set(studies)):
        chosen = _configuration_row(
            study, given.get(study), ledger.get(study), study in held, label_source
        )
        if chosen is None:
            continue
        row, label_record = chosen
        roles = objects.get(study, [])
        ids = [case["case_id"] for case in roles]
        staged = {
            "schema": memory["schema"],
            "revision": memory["revision"],
            "cases": roles,
            "object_identity_teaching": {
                **teaching,
                "confirmed_case_ids": [i for i in ids if i in confirmed],
                "calls": [call for i in ids for call in calls_by_id.get(i, ())],
            },
        }
        try:
            built, _ledger, _revision = _rebuilt_configurations(
                {"label_ledger": {study: dict(row)}}, staged
            )
        except SquintBootstrapError as error:
            raise ConfigurationProfileError(
                "configuration_rebuild_invalid", f"{study}:{error.code}"
            ) from error
        _link_configuration_full_profiles({"cases": [*roles, *built]})
        links = _role_links(staged)
        previous = dict(held.get(study, {}))
        for case in built:
            prior = previous.pop(case["case_id"], None)
            if prior is None and case["case_id"] in known:
                raise ConfigurationProfileError(
                    "configuration_case_conflict", case["case_id"]
                )
            supersedes = None if prior is None else _superseded(prior)
            case["configuration_teaching"] = {
                "schema": CONFIGURATION_TEACHING_SCHEMA,
                "labels": dict(label_record),
                "built_by": copy.deepcopy(dict(built_by)),
                "roles": {
                    subject: copy.deepcopy(links[subject])
                    for subject in sorted(case["profile"]["source"]["roles"])
                },
                "supersedes": supersedes,
            }
            result["cases"].append(case)
            if supersedes is None:
                result["new"].append(case)
            else:
                result["replaces"][case["case_id"]] = case
                result["superseded"][case["case_id"]] = supersedes["case_sha256"]
        if previous:
            raise ConfigurationProfileError(
                "configuration_rebuild_incomplete", min(previous)
            )
        if study in given and study not in ledger:
            result["label_ledger"][study] = dict(given[study])
        result["study_uids"].append(study)
    return result


def apply_rebuilt_configurations(
    memory: Mapping[str, Any], rebuilt: Mapping[str, Any]
) -> dict[str, Any]:
    """A new memory dict holding ``rebuild_study_configurations``'s cases.

    Each replacing case takes its predecessor's place in ``cases``, new ones
    follow every other case, and the supplied rows join the ``label_ledger``,
    whose rows stay as they are. Nothing else changes, the revision included;
    ``memory`` and its records are not mutated.
    """
    result = dict(memory)
    replaces = rebuilt["replaces"]
    result["cases"] = [
        *(replaces.get(case["case_id"], case) for case in memory["cases"]),
        *rebuilt["new"],
    ]
    if rebuilt["label_ledger"]:
        result["label_ledger"] = {
            **(memory.get("label_ledger") or {}),
            **rebuilt["label_ledger"],
        }
    return result


def _questions_in_order():
    from knee.diagnosis.declarations import QUESTIONS

    return QUESTIONS


def _canonical(value: dict[str, Any]) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
