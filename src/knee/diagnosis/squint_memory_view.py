"""One read-only population for location, recall and prepared comparisons.

The returned dict uses the consumers' existing shapes. As with loaded memory,
retained case/profile payloads are shared read-only; this constructor never
mutates them or its input. Population lists, portable tables, view metadata and
projected envelopes are new. No pairwise measurement runs here.
"""

from __future__ import annotations

import hashlib
import json
from collections.abc import Iterable, Mapping, Sequence
from typing import Any

from knee.diagnosis.squint_interfaces import MEMORY_VIEW_SCHEMA
from knee.diagnosis.squint_locator import recall_source_fingerprint


class MemoryViewError(ValueError):
    """A named invalid population or stale preparation refusal."""

    def __init__(self, code: str):
        self.code = code
        super().__init__(code)


def _digest(value: object) -> str:
    try:
        content = json.dumps(
            value, sort_keys=True, separators=(",", ":"), allow_nan=False
        ).encode("utf-8")
    except (TypeError, ValueError) as error:
        raise MemoryViewError("memory_view_identity_not_json") from error
    return hashlib.sha256(content).hexdigest()


def _uids(values: object) -> set[str]:
    if not isinstance(values, Iterable) or isinstance(values, (str, bytes)):
        raise MemoryViewError("memory_view_excluded_study_uids_invalid")
    try:
        result = set(values)
    except TypeError as error:
        raise MemoryViewError("memory_view_excluded_study_uids_invalid") from error
    if any(
        not isinstance(uid, str) or not uid.strip() or "\0" in uid for uid in result
    ):
        raise MemoryViewError("memory_view_excluded_study_uids_invalid")
    return result


def _rows(memory: Mapping[str, Any], key: str) -> Sequence:
    value = memory.get(key, ())
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes)):
        raise MemoryViewError(f"memory_view_{key}_invalid")
    return value


def _excluded(row: object, excluded: set[str]) -> bool:
    if not isinstance(row, Mapping):
        return False
    source = row.get("source")
    source_uid = source.get("study_uid") if isinstance(source, Mapping) else None
    uids = (row.get("study_uid"), source_uid)
    if any(uid is not None and not isinstance(uid, str) for uid in uids):
        raise MemoryViewError("memory_view_study_uid_invalid")
    return any(uid in excluded for uid in uids)


def _portable_view(memory: dict, excluded: set[str]) -> None:
    for name, key in (
        ("full_profile_contexts", "contexts"),
        ("full_profile_payloads", "payloads"),
    ):
        if name not in memory:
            continue
        table = memory[name]
        if not isinstance(table, Mapping) or not isinstance(table.get(key), Mapping):
            raise MemoryViewError("memory_view_full_profile_table_invalid")
        memory[name] = {
            **table,
            key: {
                identity: row
                for identity, row in table[key].items()
                if not _excluded(row, excluded)
            },
        }


def memory_view(
    memory: dict, *, exclude_study_uids=(), selection_version: str = "none"
) -> dict:
    """Return one immutable-revision population without the named studies.

    Exclusions compose: a view never restores a parent's excluded studies.
    ``preparation_fingerprint`` identifies the required preparation *inputs*
    (retained recall source and selection version), not sidecar file bytes.
    Missing preparation stays missing with ``recall_preparation_required``;
    stale/incompatible preparation raises a named ``MemoryViewError``. This
    constructor never rebuilds opposing comparisons, including on refusal.

    A loader may supply ``memory_manifest_sha256``. Otherwise a canonical
    manifest-content digest is used and its different scope is explicit.
    """
    if not isinstance(memory, dict):
        raise MemoryViewError("memory_view_memory_invalid")
    if not isinstance(selection_version, str) or not selection_version.strip():
        raise MemoryViewError("memory_view_selection_version_invalid")
    excluded = _uids(exclude_study_uids)
    parent = memory.get("view")
    if parent is not None:
        if (
            not isinstance(parent, Mapping)
            or parent.get("schema") != MEMORY_VIEW_SCHEMA
            or not isinstance(parent.get("manifest_identity"), Mapping)
            or parent.get("revision") != memory.get("revision", "")
        ):
            raise MemoryViewError("memory_view_parent_invalid")
        excluded.update(_uids(parent.get("excluded_study_uids", ())))
    cases = _rows(memory, "cases")
    censors = _rows(memory, "censors")
    result = {
        **memory,
        "cases": [row for row in cases if not _excluded(row, excluded)],
    }
    if "censors" in memory:
        result["censors"] = [row for row in censors if not _excluded(row, excluded)]
    if "object_identity_cases" in memory:
        # Negative identity cases and alternative-identity positives leave the
        # population with their study, exactly as its object cases do.
        table = memory["object_identity_cases"]
        rows = table.get("cases") if isinstance(table, Mapping) else None
        if not isinstance(rows, Sequence) or isinstance(rows, (str, bytes)):
            raise MemoryViewError("memory_view_object_identity_cases_invalid")
        result["object_identity_cases"] = {
            **table,
            "cases": [row for row in rows if not _excluded(row, excluded)],
        }
    result.pop("prepared_recall", None)
    result.pop("view", None)
    _portable_view(result, excluded)

    prepared_selections = (
        memory["prepared_recall"].get("selections")
        if isinstance(memory.get("prepared_recall"), Mapping)
        else None
    )
    try:
        if prepared_selections is not None:
            # A question-selected preparation fingerprints its selections too.
            source_fingerprint = recall_source_fingerprint(
                memory, selections=prepared_selections
            )
            filtered_fingerprint = recall_source_fingerprint(
                result, selections=prepared_selections
            )
        else:
            source_fingerprint = recall_source_fingerprint(memory)
            filtered_fingerprint = recall_source_fingerprint(result)
    except (TypeError, ValueError) as error:
        raise MemoryViewError("memory_view_recall_source_invalid") from error
    if parent is not None and parent.get("source_fingerprint") != source_fingerprint:
        raise MemoryViewError("memory_view_parent_source_mismatch")
    manifest_sha = memory.get("memory_manifest_sha256")
    if parent is not None:
        manifest_identity = dict(parent["manifest_identity"])
    elif manifest_sha is not None:
        if (
            not isinstance(manifest_sha, str)
            or len(manifest_sha) != 64
            or any(char not in "0123456789abcdef" for char in manifest_sha)
        ):
            raise MemoryViewError("memory_view_manifest_sha256_invalid")
        manifest_identity = {"scope": "manifest_bytes", "sha256": manifest_sha}
    else:
        manifest_identity = {
            "scope": "canonical_manifest_content",
            "sha256": _digest(
                {
                    key: value
                    for key, value in memory.items()
                    if key not in {"prepared_recall", "view", "memory_manifest_sha256"}
                }
            ),
        }
    prepared = memory.get("prepared_recall")
    code = "recall_preparation_required"
    if prepared is not None:
        if not isinstance(prepared, Mapping) or (
            prepared.get("schema") != "knee.squint-recall-preparation/v1"
            or prepared.get("outcome") != "prepared"
        ):
            raise MemoryViewError("memory_view_preparation_invalid")
        if prepared.get("source_fingerprint") != source_fingerprint:
            raise MemoryViewError("memory_view_preparation_source_mismatch")
        if prepared.get("selection_version", "none") != selection_version:
            raise MemoryViewError("memory_view_preparation_selection_mismatch")
        if "memory_revision" in prepared and prepared["memory_revision"] != memory.get(
            "revision", ""
        ):
            raise MemoryViewError("memory_view_preparation_revision_mismatch")
        if (
            "memory_manifest_sha256" in prepared
            and prepared["memory_manifest_sha256"] != manifest_identity["sha256"]
        ):
            raise MemoryViewError("memory_view_preparation_manifest_mismatch")
        if excluded:
            projected = _project_prepared_recall(
                result, prepared, excluded, filtered_fingerprint
            )
        else:
            from knee.diagnosis.squint_locator import _runtime_recall_cache

            projected = _runtime_recall_cache(result, prepared)
        if projected is None:
            raise MemoryViewError("memory_view_preparation_projection_unavailable")
        result["prepared_recall"] = projected
        code = "prepared"
    result["view"] = {
        "schema": MEMORY_VIEW_SCHEMA,
        "revision": memory.get("revision", ""),
        "manifest_identity": manifest_identity,
        "excluded_study_uids": sorted(excluded),
        "selection_version": selection_version,
        "source_fingerprint": filtered_fingerprint,
        "retained_case_ids": [
            row.get("case_id") for row in result["cases"] if isinstance(row, Mapping)
        ],
        "retained_censor_ids": [
            row.get("censor_id")
            for row in result.get("censors", ())
            if isinstance(row, Mapping)
        ],
        "preparation_fingerprint": _digest(
            {
                "schema": "knee.squint-recall-preparation/v1",
                "source_fingerprint": filtered_fingerprint,
                "selection_version": selection_version,
            }
        ),
        "preparation_code": code,
    }
    return result


def _project_prepared_recall(
    filtered_memory: Mapping[str, Any],
    prepared: Mapping[str, Any],
    excluded: set[str],
    filtered_fingerprint: str,
) -> dict[str, Any] | None:
    """Project stored comparison rows and their maxima; never remeasure pairs.

    This is the existing capacity projection, shared by both former exclusion
    paths. Only the population input and the set of excluded UIDs changed.
    """
    from knee.diagnosis.squint_locator import (
        _call,
        _condition_cases,
        _runtime_recall_cache,
        _selected_case_bank_union,
        _selection_state,
        _validated_case_banks,
    )

    cases = filtered_memory.get("cases", ())
    censors = filtered_memory.get("censors", ())
    retained_ids = {row.get("case_id") for row in cases if isinstance(row, Mapping)}
    case_indices: dict[str, dict[str, list[int]]] = {}
    questions: set[str] = set()
    # Banks are read as condition preparation reads them: identity teaching
    # lets each case speak only through the views where its identity holds.
    try:
        condition_cases = _condition_cases(filtered_memory)
    except ValueError:
        return None
    # A question-selected preparation (W7) keeps its selections: each case's
    # banks are the union of what the selected questions read.
    selections = prepared.get("selections")
    case_banks = (
        _selected_case_bank_union(_selection_state(condition_cases, selections)[1])
        if selections is not None
        else _validated_case_banks(condition_cases)
    )
    eligible_subjects = sorted(
        {
            case.get("subject")
            for index, case in enumerate(cases)
            if isinstance(case, Mapping)
            and index in case_banks
            and isinstance(case.get("subject"), str)
            and isinstance(case.get("case_id"), str)
            and isinstance(case.get("study_uid"), str)
        }
    )
    for index, case in enumerate(cases):
        if not isinstance(case, Mapping):
            continue
        calls = case.get("condition_calls", case.get("calls", {}))
        case_questions = set()
        if isinstance(calls, Mapping):
            case_questions.update(key for key in calls if isinstance(key, str) and key)
        elif isinstance(calls, Sequence) and not isinstance(calls, (str, bytes)):
            case_questions.update(
                row.get("question", row.get("condition"))
                for row in calls
                if isinstance(row, Mapping)
                and isinstance(row.get("question", row.get("condition")), str)
            )
        questions.update(case_questions)
        if selections is not None:
            case_questions.intersection_update(selections)
        subject = case.get("subject")
        if isinstance(subject, str) and isinstance(case.get("profile"), Mapping):
            for question in case_questions:
                if _call(case, question) in (-1, 1):
                    case_indices.setdefault(subject, {}).setdefault(
                        question, []
                    ).append(index)
    if selections is not None:
        questions = set(selections)
    censor_indices = {
        question: [
            index
            for index, censor in enumerate(censors)
            if isinstance(censor, Mapping)
            and censor.get("question", censor.get("condition")) == question
        ]
        for question in questions
    }
    envelopes: dict[str, dict[str, dict[str, Any]]] = {}
    source_envelopes = prepared.get("envelopes")
    if not isinstance(source_envelopes, Mapping):
        return None
    for subject in eligible_subjects:
        subject_indices = [
            index
            for index, case in enumerate(cases)
            if isinstance(case, Mapping)
            and case.get("subject") == subject
            and index in case_banks
            and isinstance(case.get("case_id"), str)
            and isinstance(case.get("study_uid"), str)
        ]
        scoped_questions = {
            question
            for question in questions
            if any(
                _call(cases[index], question) in (-1, 1) for index in subject_indices
            )
        }
        if not scoped_questions:
            continue
        subject_rows = source_envelopes.get(subject)
        if not isinstance(subject_rows, Mapping):
            return None
        for question in sorted(questions):
            scoped_indices = [
                index
                for index in subject_indices
                if _call(cases[index], question) in (-1, 1)
            ]
            if not scoped_indices:
                continue
            buckets = subject_rows.get(question, {})
            if not isinstance(buckets, Mapping):
                return None
            kept_buckets = {}
            for bucket_id, bucket in buckets.items():
                if not isinstance(bucket, Mapping):
                    return None
                comparisons = bucket.get("comparisons")
                if not isinstance(comparisons, list):
                    return None
                retained = []
                for comparison in comparisons:
                    if not isinstance(comparison, Mapping):
                        return None
                    pair_uids = comparison.get("study_uids")
                    projection = comparison.get("projection_mode")
                    ratio = comparison.get("squared_cosine")
                    if (
                        not isinstance(pair_uids, list)
                        or len(pair_uids) != 2
                        or any(not isinstance(value, str) for value in pair_uids)
                        or not isinstance(projection, str)
                        or not isinstance(ratio, Mapping)
                    ):
                        return None
                    pair_case_ids = comparison.get("case_ids")
                    if (
                        not isinstance(pair_case_ids, list)
                        or len(pair_case_ids) != 2
                        or any(not isinstance(value, str) for value in pair_case_ids)
                    ):
                        return None
                    if not excluded.intersection(pair_uids) and all(
                        case_id in retained_ids for case_id in pair_case_ids
                    ):
                        retained.append(dict(comparison))
                if not retained:
                    continue
                maximum: dict[str, int] = {}
                population_ids = []
                modes = []
                for comparison in retained:
                    ratio = comparison["squared_cosine"]
                    try:
                        numerator = int(ratio["numerator"])
                        denominator = int(ratio["denominator"])
                    except (KeyError, TypeError, ValueError):
                        return None
                    if numerator < 0 or denominator <= 0:
                        return None
                    if not maximum or numerator * maximum["denominator"] > (
                        maximum["numerator"] * denominator
                    ):
                        maximum = {"numerator": numerator, "denominator": denominator}
                    for case_id in comparison["case_ids"]:
                        if case_id not in population_ids:
                            population_ids.append(case_id)
                    if comparison["projection_mode"] not in modes:
                        modes.append(comparison["projection_mode"])
                projected = {
                    **bucket,
                    "projection_modes": modes,
                    "population_case_ids": population_ids,
                    "independent_comparison_count": len(retained),
                    "maximum_squared_cosine": {
                        "numerator": str(maximum["numerator"]),
                        "denominator": str(maximum["denominator"]),
                    },
                    "comparisons": retained,
                }
                kept_buckets[bucket_id] = projected
            envelopes.setdefault(subject, {})[question] = kept_buckets
    stored = {
        **prepared,
        "memory_source": filtered_memory.get(
            "source", filtered_memory.get("metadata", {})
        ),
        "source_fingerprint": filtered_fingerprint,
        "envelopes": envelopes,
        "case_indices": case_indices,
        "censor_indices": censor_indices,
    }
    if selections is not None:
        stored["selection_identity"] = _selection_state(condition_cases, selections)[0]
    runtime = _runtime_recall_cache(filtered_memory, stored)
    if runtime is None:
        return None
    runtime.pop("excluded_study_uid", None)
    runtime["excluded_study_uids"] = sorted(excluded)
    if len(excluded) == 1:
        runtime["excluded_study_uid"] = next(iter(excluded))
    return runtime
