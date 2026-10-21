"""Squint-first object localization and individual-case recall.

The public exchange is deliberately mapping based. Count comparisons are exact
integer comparisons; absent banks are silence and never become a zero vote.
"""

from __future__ import annotations

import hashlib
import json
import math
import time
from collections.abc import Mapping, Sequence
from decimal import Decimal, InvalidOperation
from typing import Any

import numpy as np

RECALL_CACHE_SCHEMA = "knee.squint-recall-cache/v1"
_UNSELECTED = object()


def _selection_names(
    selection: Mapping[str, Any], subject: str, banks: Mapping
) -> tuple[str, ...]:
    """Use W6's one selector for object banks and qualified configuration roles."""
    from knee.diagnosis.squint_questions import select_cheap_banks

    if subject in selection["subjects"]:
        names, _code = select_cheap_banks(selection, subject, banks)
        return names
    configuration = selection.get(
        "configuration_subject", "diagnosis/" + selection["question_id"]
    )
    if subject != configuration:
        return ()
    names = set()
    for role_subject in selection["subjects"]:
        qualified = {
            name: counts
            for name, counts in banks.items()
            if name.startswith(f"object/{role_subject}/")
        }
        selected, _code = select_cheap_banks(selection, role_subject, qualified)
        names.update(selected)
    return tuple(sorted(names))


def _selection_digest(selection: Mapping[str, Any]) -> str:
    """Bind the complete declaration, not a caller-supplied fingerprint alone."""
    payload = json.dumps(
        selection, sort_keys=True, separators=(",", ":"), allow_nan=False
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _selected_profile_banks(
    selection: Mapping[str, Any], subject: str, profile: object
) -> dict[str, tuple[int, ...]] | None:
    """Select names before reading or validating any count payload."""
    if not isinstance(profile, Mapping) or not isinstance(
        profile.get("banks"), Mapping
    ):
        return None
    raw = profile["banks"]
    names = _selection_names(selection, subject, raw)
    return _banks({"banks": {name: raw[name] for name in names}})


def _selected_case_bank_union(question_banks: Mapping) -> dict:
    result: dict = {}
    for by_case in question_banks.values():
        for index, banks in by_case.items():
            result.setdefault(index, {}).update(banks)
    return result


def _selection_state(
    cases: Sequence, selections: Mapping[str, Any]
) -> tuple[dict, dict]:
    """Project banks before matrices/envelopes; retain selected tuples in identity."""
    from knee.diagnosis.squint_interfaces import selection_code

    identities, question_banks = {}, {}
    for question, selection in selections.items():
        code = selection_code(selection)
        if code != "valid":
            raise ValueError(code)
        if question != selection["question_id"]:
            raise ValueError("selection_question_mismatch")
        if not selection["cheap"]:
            raise ValueError("selection_empty")
        by_case, by_subject = {}, {}
        for index, case in enumerate(cases):
            if not isinstance(case, Mapping) or not isinstance(
                case.get("subject"), str
            ):
                continue
            subject = case["subject"]
            banks = _selected_profile_banks(selection, subject, case.get("profile"))
            if banks is None:
                continue
            procedure = selection.get("cheap_procedure")
            names = (
                tuple(banks)
                if procedure is None
                or procedure == _source(case.get("profile")).get("procedure")
                else ()
            )
            by_case[index] = {name: banks[name] for name in names}
            by_subject.setdefault(subject, set()).update(names)
        identities[question] = {
            "schema": selection["schema"],
            "version": selection["version"],
            "descriptor_sha256": _selection_digest(selection),
            "selected_banks": {
                subject: sorted(names) for subject, names in sorted(by_subject.items())
            },
        }
        question_banks[question] = by_case
    return identities, question_banks


def _declared_selections(memory: Mapping[str, Any], selections: object) -> dict | None:
    """Explicit declarations, or W6 for v2 memory; v1 API callers stay readable."""
    if selections is _UNSELECTED:
        selections = memory.get("recall_selections", _UNSELECTED)
    if selections is _UNSELECTED:
        from knee.diagnosis.squint_interfaces import TERRITORY_PROCEDURE

        cases = memory.get("cases", ())
        if not any(
            isinstance(case, Mapping)
            and _source(case.get("profile")).get("procedure") == TERRITORY_PROCEDURE
            for case in cases
        ):
            return None
        from knee.diagnosis.squint_questions import question_selection

        questions = {
            question
            for case in cases
            if isinstance(case, Mapping)
            for question in _case_questions(case)
        }
        selections = {
            question: question_selection(question) for question in sorted(questions)
        }
    if not isinstance(selections, Mapping):
        raise TypeError("selections_mapping_required")
    if not selections:
        raise ValueError("selection_empty")
    return dict(selections)


def _case_questions(case: Mapping[str, Any]) -> set[str]:
    calls = case.get("condition_calls", case.get("calls", {}))
    if isinstance(calls, Mapping):
        return {name for name in calls if isinstance(name, str) and name}
    if isinstance(calls, Sequence) and not isinstance(calls, (str, bytes)):
        return {
            row.get("question", row.get("condition"))
            for row in calls
            if isinstance(row, Mapping)
            and isinstance(row.get("question", row.get("condition")), str)
        }
    return set()


def recall_source_fingerprint(
    memory: Mapping[str, Any], *, selections: object = _UNSELECTED
) -> str:
    """Fingerprint exactly the case/censor inputs consumed by recall preparation."""
    cases = memory.get("cases", ())
    if not isinstance(cases, Sequence) or isinstance(cases, (str, bytes)):
        raise TypeError("memory_cases_required")
    source_cases = []
    for case in cases:
        if not isinstance(case, Mapping):
            source_cases.append(case)
            continue
        source_cases.append(
            {
                "case_id": case.get("case_id"),
                "study_uid": case.get("study_uid"),
                "subject": case.get("subject"),
                "calls": case.get("condition_calls", case.get("calls", {})),
                "profile": case.get("profile"),
            }
        )
    censors = memory.get("censors", ())
    payload = {
        "schema": "knee.squint-recall-input/v1",
        "memory_source": memory.get("source", memory.get("metadata", {})),
        "cases": source_cases,
        "censors": censors,
    }
    selected = _declared_selections(memory, selections)
    if selected is not None:
        payload["selection_identity"] = _selection_state(cases, selected)[0]
    try:
        encoded = json.dumps(
            payload, sort_keys=True, separators=(",", ":"), allow_nan=False
        ).encode("utf-8")
    except (TypeError, ValueError) as error:
        raise ValueError("memory_recall_input_not_json") from error
    return hashlib.sha256(encoded).hexdigest()


def _runtime_recall_cache(
    memory: Mapping[str, Any], stored: Mapping[str, Any]
) -> dict[str, Any] | None:
    """Rebuild only cheap integer bank indexes/matrices around stored envelopes."""
    cases = memory.get("cases", ())
    raw_indices = stored.get("case_indices")
    raw_censor_indices = stored.get("censor_indices")
    envelopes = stored.get("envelopes")
    if not isinstance(raw_indices, Mapping) or not isinstance(envelopes, Mapping):
        return None
    if not isinstance(raw_censor_indices, Mapping):
        return None
    for subject, questions in raw_indices.items():
        if not isinstance(subject, str) or not isinstance(questions, Mapping):
            return None
        for question, indexes in questions.items():
            if not isinstance(question, str) or not isinstance(indexes, list):
                return None
            if any(
                type(index) is not int
                or not 0 <= index < len(cases)
                or not isinstance(cases[index], Mapping)
                or cases[index].get("subject") != subject
                or _call(cases[index], question) not in (-1, 1)
                for index in indexes
            ):
                return None
    censors = memory.get("censors", ())
    if not isinstance(censors, Sequence) or isinstance(censors, (str, bytes)):
        censors = ()
    for question, indexes in raw_censor_indices.items():
        if not isinstance(question, str) or not isinstance(indexes, list):
            return None
        if any(
            type(index) is not int
            or not 0 <= index < len(censors)
            or not isinstance(censors[index], Mapping)
            or censors[index].get("question", censors[index].get("condition"))
            != question
            for index in indexes
        ):
            return None
    selections = stored.get("selections")
    identities, question_banks = {}, {}
    if selections is None:
        try:
            if _declared_selections(memory, _UNSELECTED) is not None:
                return None
        except (ImportError, TypeError, ValueError):
            return None
    if selections is not None:
        try:
            identities, question_banks = _selection_state(cases, selections)
        except (ImportError, TypeError, ValueError):
            return None
        if stored.get("selection_identity") != identities:
            return None
    case_banks = (
        _selected_case_bank_union(question_banks)
        if selections is not None
        else _validated_case_banks(cases)
    )
    subjects = sorted(
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
    matrices: dict[str, dict[str, Any]] = {}
    question_matrices: dict[str, dict[str, Any]] = {}
    for subject in subjects:
        indexes = [
            index
            for index, case in enumerate(cases)
            if isinstance(case, Mapping) and case.get("subject") == subject
        ]
        if selections is None:
            matrices[subject] = _case_matrix(
                [case_banks.get(index) for index in indexes], indexes
            )
        else:
            for question, banks in question_banks.items():
                question_matrices.setdefault(subject, {})[question] = _case_matrix(
                    [banks.get(index) for index in indexes], indexes
                )
    return {
        **stored,
        "case_profile_banks": case_banks,
        "subject_profile_matrices": matrices,
        "question_case_profile_banks": question_banks,
        "question_profile_matrices": question_matrices,
        "runtime_indexes_rebuilt": True,
    }


def _memory_without_study(memory: Mapping[str, Any], uid: str) -> dict[str, Any]:
    """Delegate capacity's population construction to the shared memory view."""
    from knee.diagnosis.squint_memory_view import memory_view

    return memory_view(dict(memory), exclude_study_uids=(uid,))


def _project_recall_cache_without_study(
    memory: Mapping[str, Any], prepared: Mapping[str, Any], uid: str
) -> dict[str, Any] | None:
    """Delegate exact cached comparison projection to the shared memory view."""
    from knee.diagnosis.squint_memory_view import MemoryViewError, memory_view

    try:
        view = memory_view(
            {**memory, "prepared_recall": prepared}, exclude_study_uids=(uid,)
        )
    except MemoryViewError:
        # prepare_recall retains its existing legacy-cache rebuild behavior.
        return None
    return view["prepared_recall"]


def _mapping(value: object) -> Mapping[str, Any] | None:
    return value if isinstance(value, Mapping) else None


def _banks(profile: object) -> dict[str, tuple[int, ...]] | None:
    """Read a squint-profile/v1 bank mapping or the existing typed Profile."""
    if isinstance(profile, Mapping):
        raw = profile.get("banks")
        if not isinstance(raw, Mapping):
            return None
        result: dict[str, tuple[int, ...]] = {}
        for name, counts in raw.items():
            if not isinstance(name, str) or not name:
                return None
            if not isinstance(counts, (tuple, list)) or len(counts) != 3:
                return None
            if any(type(value) is not int or value < 0 for value in counts):
                return None
            result[name] = tuple(counts)
        return result
    bundle = getattr(profile, "bundle", None)
    layout = getattr(bundle, "layout", None)
    counts = getattr(bundle, "counts", None)
    bank_layouts = getattr(layout, "banks", None)
    if not isinstance(bank_layouts, tuple) or not isinstance(counts, tuple):
        return None
    if len(bank_layouts) != len(counts):
        return None
    result = {}
    for bank, rows in zip(bank_layouts, counts, strict=True):
        name = getattr(bank, "name", None)
        if not isinstance(name, str) or not name or not isinstance(rows, tuple):
            return None
        if any(type(value) is not int or value < 0 for value in rows):
            return None
        result[name] = rows
    return result


def _subject(profile: object) -> str | None:
    value = _mapping(profile)
    subject = (
        value.get("subject") if value is not None else getattr(profile, "subject", None)
    )
    return subject if isinstance(subject, str) and subject else None


def _source(profile: object) -> dict[str, Any]:
    value = _mapping(profile)
    if value is not None:
        source = value.get("source", value.get("source_metadata", {}))
        return dict(source) if isinstance(source, Mapping) else {}
    provenance = getattr(profile, "provenance", ())
    return (
        {key: item for key, item in provenance if isinstance(key, str)}
        if isinstance(provenance, tuple)
        else {}
    )


def _same_procedure(left: object, right: object) -> bool:
    return _source(left).get("procedure") == _source(right).get("procedure")


def _coarse_only_projection(profile: object) -> dict[str, Any] | None:
    """Project a complete profile onto the scan's original 10 mm banks."""
    value = _mapping(profile)
    banks = _banks(profile)
    if value is None or banks is None:
        return None
    coarse: dict[str, list[int]] = {}
    for name, counts in banks.items():
        scale = name.rsplit("/scale=", 1)[-1] if "/scale=" in name else ""
        if not scale.endswith("mm"):
            continue
        try:
            is_coarse = Decimal(scale[:-2]) == Decimal(10)
        except InvalidOperation:
            is_coarse = False
        if is_coarse:
            coarse[name] = list(counts)
    return {
        "schema": value.get("schema", "knee.squint-profile/v1"),
        "subject": value.get("subject"),
        "banks": coarse,
        "source": dict(value.get("source", {}))
        if isinstance(value.get("source"), Mapping)
        else {},
    }


def _terms(left: object, right: object) -> dict[str, Any] | None:
    left_banks, right_banks = _banks(left), _banks(right)
    if left_banks is None or right_banks is None:
        return None
    if isinstance(left, Mapping) and isinstance(right, Mapping):
        try:
            from knee.diagnosis.squint_profiles import cosine_evidence
        except ImportError:
            cosine_evidence = None
        if cosine_evidence is not None:
            shared = cosine_evidence(dict(left), dict(right))
            if not isinstance(shared, Mapping):
                return None
            if shared.get("code") == "identity_mismatch":
                return None
            if shared.get("code") != "ok":
                return {"code": "silent", "common_speaking_banks": []}
            dot = shared.get("dot")
            left_sq = shared.get("left_norm_sq")
            right_sq = shared.get("right_norm_sq")
            included = shared.get("common_banks")
            if (
                any(
                    type(value) is not int or value < 0
                    for value in (dot, left_sq, right_sq)
                )
                or not isinstance(included, (list, tuple))
                or any(not isinstance(name, str) for name in included)
                or left_sq == 0
                or right_sq == 0
            ):
                return None
            return {
                "code": "ok",
                "dot": dot,
                "left_norm_sq": left_sq,
                "right_norm_sq": right_sq,
                "common_speaking_banks": list(included),
                "cosine_squared": (dot * dot, left_sq * right_sq),
            }
    common = sorted(set(left_banks) & set(right_banks))
    dot = left_sq = right_sq = 0
    included: list[str] = []
    for bank in common:
        a, b = left_banks[bank], right_banks[bank]
        if len(a) != len(b):
            return None
        if not any(a) or not any(b):
            continue
        included.append(bank)
        dot += sum(x * y for x, y in zip(a, b, strict=True))
        left_sq += sum(x * x for x in a)
        right_sq += sum(y * y for y in b)
    if not included:
        return {"code": "silent", "common_speaking_banks": []}
    return {
        "code": "ok",
        "dot": dot,
        "left_norm_sq": left_sq,
        "right_norm_sq": right_sq,
        "common_speaking_banks": included,
        "cosine_squared": (dot * dot, left_sq * right_sq),
    }


_INT64_MAX = int(np.iinfo(np.int64).max)


def _exact_bank_terms(
    left_banks: Mapping[str, Sequence[int]],
    right_banks: Mapping[str, Sequence[int]],
) -> dict[str, Any]:
    """Compute exact cosine terms from already validated count banks."""
    common = sorted(set(left_banks) & set(right_banks))
    dot = left_sq = right_sq = 0
    included: list[str] = []
    for bank in common:
        left = left_banks[bank]
        right = right_banks[bank]
        if not any(left) or not any(right):
            continue
        included.append(bank)
        dot += sum(a * b for a, b in zip(left, right, strict=True))
        left_sq += sum(value * value for value in left)
        right_sq += sum(value * value for value in right)
    if not included:
        return {"code": "silent", "common_speaking_banks": []}
    return {
        "code": "ok",
        "dot": dot,
        "left_norm_sq": left_sq,
        "right_norm_sq": right_sq,
        "common_speaking_banks": included,
        "cosine_squared": (dot * dot, left_sq * right_sq),
    }


def _validated_case_banks(
    cases: Sequence[Mapping[str, Any]],
) -> dict[int, dict[str, tuple[int, ...]]]:
    """Validate case profiles once and retain their exact integer banks."""
    result: dict[int, dict[str, tuple[int, ...]]] = {}
    for index, case in enumerate(cases):
        if not isinstance(case, Mapping):
            continue
        banks = _banks(case.get("profile"))
        if banks is not None:
            result[index] = banks
    return result


def _case_matrix(
    indexed_banks: Sequence[Mapping[str, Sequence[int]] | None],
    case_indices: Sequence[int] | None = None,
) -> dict[str, Any]:
    """Precompute case bank vectors and prove whether int64 arithmetic is safe."""
    names = tuple(
        sorted({name for row in indexed_banks if row is not None for name in row})
    )
    max_count = max(
        (
            value
            for row in indexed_banks
            if row is not None
            for counts in row.values()
            for value in counts
        ),
        default=0,
    )
    dimensions = max(1, len(names) * 3)
    safe = max_count == 0 or max_count <= math.isqrt(_INT64_MAX // dimensions)
    dtype = np.int64 if safe else object
    matrix = np.zeros((len(indexed_banks), len(names), 3), dtype=dtype)
    speaks = np.zeros((len(indexed_banks), len(names)), dtype=np.bool_)
    valid = np.zeros(len(indexed_banks), dtype=np.bool_)
    positions = {name: index for index, name in enumerate(names)}
    for row_index, row in enumerate(indexed_banks):
        if row is None:
            continue
        valid[row_index] = True
        for name, counts in row.items():
            bank_index = positions[name]
            matrix[row_index, bank_index] = counts
            speaks[row_index, bank_index] = any(counts)
    return {
        "names": names,
        "values": matrix,
        "speaks": speaks,
        "valid": valid,
        "max_count": max_count,
        "safe_int64": safe,
        "row_by_case": {
            case_index: row_index
            for row_index, case_index in enumerate(
                case_indices or range(len(indexed_banks))
            )
        },
    }


def _batch_terms(
    query_banks: Mapping[str, Sequence[int]],
    indexed_banks: Sequence[Mapping[str, Sequence[int]] | None],
    *,
    matrix_cache: Mapping[str, Any] | None = None,
    compatible: Sequence[bool] | None = None,
    row_indices: Sequence[int] | None = None,
) -> list[dict[str, Any] | None]:
    """Compare one query to cached case vectors with exact integer arithmetic."""
    if matrix_cache is None:
        matrix_cache = _case_matrix(indexed_banks)
    cached_names = matrix_cache["names"]
    names = tuple(sorted(set(cached_names) | set(query_banks)))
    full_matrix = matrix_cache["values"]
    if row_indices is None and len(indexed_banks) != len(full_matrix):
        raise ValueError("case_matrix_length_mismatch")
    if row_indices is None:
        selected_rows = list(range(len(full_matrix)))
    else:
        row_by_case = matrix_cache["row_by_case"]
        selected_rows = [row_by_case[index] for index in row_indices]
        if len(indexed_banks) != len(selected_rows):
            raise ValueError("selected_case_matrix_length_mismatch")
    matrix = full_matrix[selected_rows]
    speaks = matrix_cache["speaks"][selected_rows]
    valid = matrix_cache["valid"][selected_rows]
    dimensions = max(1, len(names) * 3)
    query_max = max(
        (value for counts in query_banks.values() for value in counts), default=0
    )
    maximum = max(matrix_cache["max_count"], query_max)
    safe_int64 = maximum == 0 or maximum <= math.isqrt(_INT64_MAX // dimensions)
    dtype = np.int64 if safe_int64 else object
    if matrix.dtype != np.dtype(dtype):
        matrix = matrix.astype(dtype, copy=False)
    if len(names) != len(cached_names):
        expanded = np.zeros((len(matrix), len(names), 3), dtype=dtype)
        expanded_speaks = np.zeros((len(matrix), len(names)), dtype=np.bool_)
        new_positions = {name: index for index, name in enumerate(names)}
        old_positions = [new_positions[name] for name in cached_names]
        expanded[:, old_positions, :] = matrix
        expanded_speaks[:, old_positions] = speaks
        matrix, speaks = expanded, expanded_speaks
    query = np.zeros((len(names), 3), dtype=dtype)
    query_speaks = np.zeros(len(names), dtype=np.bool_)
    positions = {name: index for index, name in enumerate(names)}
    for name, counts in query_banks.items():
        bank_index = positions.get(name)
        if bank_index is not None:
            query[bank_index] = counts
            query_speaks[bank_index] = any(counts)
    shared = speaks & query_speaks[None, :]
    left = np.where(shared[:, :, None], query[None, :, :], 0)
    right = np.where(shared[:, :, None], matrix, 0)
    dots = np.sum(left * right, axis=(1, 2), dtype=dtype)
    left_norms = np.sum(left * left, axis=(1, 2), dtype=dtype)
    right_norms = np.sum(right * right, axis=(1, 2), dtype=dtype)
    output: list[dict[str, Any] | None] = []
    for index, (dot, left_sq, right_sq) in enumerate(
        zip(dots, left_norms, right_norms, strict=True)
    ):
        if not valid[index] or (compatible is not None and not compatible[index]):
            output.append(None)
            continue
        speaking = [names[j] for j in np.flatnonzero(shared[index])]
        if not speaking or not left_sq or not right_sq:
            output.append({"code": "silent", "common_speaking_banks": []})
            continue
        dot_i, left_i, right_i = int(dot), int(left_sq), int(right_sq)
        output.append(
            {
                "code": "ok",
                "dot": dot_i,
                "left_norm_sq": left_i,
                "right_norm_sq": right_i,
                "common_speaking_banks": speaking,
                "cosine_squared": (dot_i * dot_i, left_i * right_i),
            }
        )
    return output


def _call(case: Mapping[str, Any], question: str) -> int | None:
    calls = case.get("condition_calls", case.get("calls", {}))
    if isinstance(calls, Mapping):
        value = calls.get(question)
        if isinstance(value, Mapping):
            value = value.get("digit", value.get("call"))
        return value if type(value) is int and value in (-1, 0, 1) else None
    if isinstance(calls, Sequence) and not isinstance(calls, (str, bytes)):
        matches = [
            row
            for row in calls
            if isinstance(row, Mapping)
            and row.get("question", row.get("condition")) == question
        ]
        if len(matches) == 1:
            value = matches[0].get("digit", matches[0].get("call"))
            return value if type(value) is int and value in (-1, 0, 1) else None
    return None


def _case_call_scope(case: Mapping[str, Any], question: str) -> str | None:
    """Return the exact nonempty per-question presentation scope, if present."""
    scopes = case.get("presentation_scope")
    if not isinstance(scopes, Mapping):
        return None
    value = scopes.get(question)
    return value if isinstance(value, str) and value else None


def _question_id(question: object) -> str | None:
    if isinstance(question, str) and question:
        return question
    if isinstance(question, Mapping):
        value = question.get("question_id", question.get("condition"))
        return value if isinstance(value, str) and value else None
    return None


def prepare_recall(
    memory: dict,
    *,
    cached: Mapping[str, Any] | None = None,
    exclude_study_uid: str = "",
    selections: object = _UNSELECTED,
    selection: object = _UNSELECTED,
) -> dict:
    """Prepare immutable empirical opposing-case resemblance envelopes.

    Each envelope records the maximum exact squared cosine between independent
    cases with opposing calls, using their jointly speaking banks. It is a
    finite empirical bound, not a calibrated probability.
    """
    if not isinstance(memory, dict):
        return {"outcome": "invalid_input", "reason": "memory_must_be_object"}
    cases = memory.get("cases")
    if not isinstance(cases, Sequence) or isinstance(cases, (str, bytes)):
        return {"outcome": "invalid_input", "reason": "memory_cases_required"}
    if exclude_study_uid and (
        not isinstance(exclude_study_uid, str) or not exclude_study_uid
    ):
        return {"outcome": "invalid_input", "reason": "excluded_study_uid_invalid"}
    if selection is not _UNSELECTED:
        if selections is not _UNSELECTED:
            return {
                "outcome": "invalid_selection",
                "reason": "selection_arguments_conflict",
            }
        selections = (
            {selection.get("question_id"): selection}
            if isinstance(selection, Mapping)
            else selection
        )
    try:
        selections = _declared_selections(memory, selections)
        selection_identity, question_banks = (
            _selection_state(cases, selections) if selections is not None else ({}, {})
        )
    except ImportError:
        return {
            "outcome": "invalid_selection",
            "reason": "question_selector_unavailable",
        }
    except (TypeError, ValueError) as error:
        return {"outcome": "invalid_selection", "reason": str(error)}
    selection_args: dict[str, Any] = (
        {"selections": selections} if selections is not None else {}
    )
    cache_status = None
    if cached is not None:
        try:
            fingerprint = recall_source_fingerprint(memory, **selection_args)
        except ValueError:
            return {"outcome": "invalid_input", "reason": "memory_recall_input_invalid"}
        stored = (
            cached.get("preparation")
            if cached.get("schema") == RECALL_CACHE_SCHEMA
            else None
        )
        if (
            isinstance(stored, Mapping)
            and cached.get("source_fingerprint") == fingerprint
            and stored.get("source_fingerprint") == fingerprint
            and stored.get("schema") == "knee.squint-recall-preparation/v1"
            and stored.get("outcome") == "prepared"
            and stored.get("selection_identity", {}) == selection_identity
            and ("selections" in stored) == (selections is not None)
            and cached.get("censor_count") == len(memory.get("censors", ()))
        ):
            runtime = _runtime_recall_cache(memory, stored)
            if runtime is not None:
                if not exclude_study_uid:
                    return runtime
                projected = _project_recall_cache_without_study(
                    memory, runtime, exclude_study_uid
                )
                if projected is not None:
                    return projected
        if exclude_study_uid:
            rebuilt = prepare_recall(
                _memory_without_study(memory, exclude_study_uid), **selection_args
            )
            rebuilt["cache_status"] = "rebuilt_incompatible_cache"
            return rebuilt
        cache_status = (
            "rebuilt_selection_identity_mismatch"
            if selections is not None
            and (
                not isinstance(stored, Mapping)
                or stored.get("selection_identity") != selection_identity
            )
            else "rebuilt_incompatible_cache"
        )
    elif exclude_study_uid:
        return prepare_recall(
            _memory_without_study(memory, exclude_study_uid), **selection_args
        )
    envelopes: dict[str, dict[str, dict[str, Any]]] = {}
    case_indices: dict[str, dict[str, list[int]]] = {}
    censor_indices: dict[str, list[int]] = {}
    questions: set[str] = set()
    for case in cases:
        if not isinstance(case, Mapping):
            continue
        calls = case.get("condition_calls", case.get("calls", {}))
        if isinstance(calls, Mapping):
            questions.update(key for key in calls if isinstance(key, str) and key)
        elif isinstance(calls, Sequence) and not isinstance(calls, (str, bytes)):
            questions.update(
                row.get("question", row.get("condition"))
                for row in calls
                if isinstance(row, Mapping)
                and isinstance(row.get("question", row.get("condition")), str)
            )
    case_banks = (
        _selected_case_bank_union(question_banks)
        if selections is not None
        else _validated_case_banks(cases)
    )
    if selections is not None:
        questions = set(selections)
    subject_profile_matrices: dict[str, dict[str, Any]] = {}
    question_profile_matrices: dict[str, dict[str, Any]] = {}
    subjects = sorted(
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
    pair_cache: dict[tuple, list[tuple[str, dict[str, Any]]]] = {}

    def pair_projections(
        first_index: int, second_index: int, question: str
    ) -> list[tuple[str, dict[str, Any]]]:
        scoped_banks = (
            question_banks[question] if selections is not None else case_banks
        )
        first_banks = scoped_banks.get(first_index)
        second_banks = scoped_banks.get(second_index)
        if first_banks is None or second_banks is None:
            return []
        key = (first_index, second_index, tuple(first_banks), tuple(second_banks))
        cached = pair_cache.get(key)
        if cached is not None:
            return cached
        projected: list[tuple[str, dict[str, Any]]] = []
        if not _same_procedure(
            cases[first_index].get("profile"), cases[second_index].get("profile")
        ):
            pair_cache[key] = projected
            return projected
        full = _exact_bank_terms(first_banks, second_banks)
        if full["code"] == "ok":
            projected.append(("full", full))
        first_coarse = {
            name: counts
            for name, counts in first_banks.items()
            if name.rsplit("/scale=", 1)[-1] == "10mm"
        }
        second_coarse = {
            name: counts
            for name, counts in second_banks.items()
            if name.rsplit("/scale=", 1)[-1] == "10mm"
        }
        if first_coarse and second_coarse:
            coarse = _exact_bank_terms(first_coarse, second_coarse)
            if coarse["code"] == "ok":
                projected.append(("coarse_10mm", coarse))
        pair_cache[key] = projected
        return projected

    for subject in subjects:
        subject_indices = [
            index
            for index, case in enumerate(cases)
            if isinstance(case, Mapping)
            and case.get("subject") == subject
            and index in case_banks
            and isinstance(case.get("case_id"), str)
            and isinstance(case.get("study_uid"), str)
        ]
        all_subject_indices = [
            index
            for index, case in enumerate(cases)
            if isinstance(case, Mapping) and case.get("subject") == subject
        ]
        if selections is None:
            subject_profile_matrices[subject] = _case_matrix(
                [case_banks.get(index) for index in all_subject_indices],
                all_subject_indices,
            )
        else:
            for question, banks in question_banks.items():
                question_profile_matrices.setdefault(subject, {})[question] = (
                    _case_matrix(
                        [banks.get(index) for index in all_subject_indices],
                        all_subject_indices,
                    )
                )
        for question in sorted(questions):
            scoped_indices = [
                index
                for index in subject_indices
                if _call(cases[index], question) in (-1, 1)
            ]
            if not scoped_indices:
                continue
            indices = [
                index
                for index, case in enumerate(cases)
                if isinstance(case, Mapping)
                and case.get("subject") == subject
                and _call(case, question) in (-1, 1)
                and isinstance(case.get("profile"), Mapping)
            ]
            case_indices.setdefault(subject, {})[question] = indices
            buckets: dict[str, dict[str, Any]] = {}
            for ordinal, first_index in enumerate(scoped_indices):
                first = cases[first_index]
                for second_index in scoped_indices[ordinal + 1 :]:
                    second = cases[second_index]
                    if first["study_uid"] == second["study_uid"] or _call(
                        first, question
                    ) == _call(second, question):
                        continue
                    for mode, evidence in pair_projections(
                        first_index, second_index, question
                    ):
                        bank_names = tuple(evidence["common_speaking_banks"])
                        bank_key = json.dumps(bank_names, separators=(",", ":"))
                        envelope = buckets.get(bank_key)
                        if envelope is None:
                            envelope = {
                                "available": True,
                                "source": "finite_empirical_opposing_case_resemblance_envelope",
                                "question": question,
                                "subject": subject,
                                "mode": _source(first["profile"]).get("procedure"),
                                "banks": list(bank_names),
                                "projection_modes": [],
                                "population_case_ids": [],
                                "independent_comparison_count": 0,
                                "maximum_squared_cosine": None,
                                "comparisons": [],
                                "calibrated_probability": False,
                            }
                            buckets[bank_key] = envelope
                        if mode not in envelope["projection_modes"]:
                            envelope["projection_modes"].append(mode)
                        ratio = evidence["cosine_squared"]
                        envelope["independent_comparison_count"] += 1
                        for case_id in (first["case_id"], second["case_id"]):
                            if case_id not in envelope["population_case_ids"]:
                                envelope["population_case_ids"].append(case_id)
                        maximum = envelope["maximum_squared_cosine"]
                        if (
                            maximum is None
                            or ratio[0] * int(maximum["denominator"])
                            > int(maximum["numerator"]) * ratio[1]
                        ):
                            envelope["maximum_squared_cosine"] = {
                                "numerator": str(ratio[0]),
                                "denominator": str(ratio[1]),
                            }
                        envelope["comparisons"].append(
                            {
                                "case_ids": [first["case_id"], second["case_id"]],
                                "study_uids": [first["study_uid"], second["study_uid"]],
                                "projection_mode": mode,
                                "common_speaking_banks": evidence[
                                    "common_speaking_banks"
                                ],
                                "squared_cosine": {
                                    "numerator": str(ratio[0]),
                                    "denominator": str(ratio[1]),
                                },
                            }
                        )
            envelopes.setdefault(subject, {})[question] = buckets
    for question in sorted(questions):
        censor_indices[question] = (
            [
                index
                for index, censor in enumerate(memory.get("censors", ()))
                if isinstance(censor, Mapping)
                and censor.get("question", censor.get("condition")) == question
            ]
            if isinstance(memory.get("censors", ()), Sequence)
            else []
        )
    result = {
        "outcome": "prepared",
        "schema": "knee.squint-recall-preparation/v1",
        "memory_source": memory.get("source", memory.get("metadata", {})),
        "source_fingerprint": recall_source_fingerprint(memory, **selection_args),
        "envelopes": envelopes,
        "case_indices": case_indices,
        "censor_indices": censor_indices,
        "case_profile_banks": case_banks,
        "subject_profile_matrices": subject_profile_matrices,
    }
    if selections is not None:
        result.update(
            selections=selections,
            selection_identity=selection_identity,
            question_case_profile_banks=question_banks,
            question_profile_matrices=question_profile_matrices,
        )
    if cache_status is not None:
        result["cache_status"] = cache_status
    return result


def persisted_recall_cache(
    memory: Mapping[str, Any], prepared: Mapping[str, Any]
) -> dict[str, Any]:
    """Return JSON-safe invariant preparation bound to its exact source fields."""
    selections = prepared.get("selections")
    fingerprint = recall_source_fingerprint(
        memory, selections=selections if selections is not None else _UNSELECTED
    )
    if (
        prepared.get("schema") != "knee.squint-recall-preparation/v1"
        or prepared.get("outcome") != "prepared"
        or prepared.get("source_fingerprint") != fingerprint
    ):
        raise ValueError("recall_preparation_source_mismatch")
    if (
        selections is not None
        and prepared.get("selection_identity")
        != _selection_state(memory.get("cases", ()), selections)[0]
    ):
        raise ValueError("recall_preparation_selection_identity_mismatch")
    return {
        "schema": RECALL_CACHE_SCHEMA,
        "source_fingerprint": fingerprint,
        "censor_count": len(memory.get("censors", ())),
        "preparation": {
            key: prepared[key]
            for key in (
                "outcome",
                "schema",
                "source_fingerprint",
                "memory_source",
                "envelopes",
                "case_indices",
                "censor_indices",
            )
            + (("selections", "selection_identity") if selections is not None else ())
        },
    }


def _profile_candidates(
    study: Mapping[str, Any],
) -> tuple[list[Mapping[str, Any]], list[str]]:
    raw = study.get("series", ())
    series = (
        list(raw)
        if isinstance(raw, Sequence) and not isinstance(raw, (str, bytes))
        else []
    )
    available = [item for item in series if isinstance(item, Mapping)]
    return available, [str(item.get("series_uid", "")) for item in available]


def _view_key(value: object) -> tuple[str, str, str] | None:
    if not isinstance(value, Mapping):
        return None
    parts = tuple(
        value.get(key) for key in ("orientation", "fluid_sensitive", "fat_suppression")
    )
    if any(not isinstance(part, str) for part in parts):
        return None
    return parts  # type: ignore[return-value]


def _case_regions(case: Mapping[str, Any], subject: str) -> list[Mapping[str, Any]]:
    regions = case.get("regions", {})
    if isinstance(regions, Mapping):
        value = regions.get(subject, ())
        return (
            [item for item in value if isinstance(item, Mapping)]
            if isinstance(value, Sequence) and not isinstance(value, (str, bytes))
            else [value]
            if isinstance(value, Mapping)
            else []
        )
    if isinstance(regions, Sequence) and not isinstance(regions, (str, bytes)):
        return [
            item
            for item in regions
            if isinstance(item, Mapping)
            and item.get("subject", item.get("object", subject)) == subject
        ]
    return []


def _window_size(
    region: Mapping[str, Any], profile: object
) -> tuple[int, int, int] | None:
    """Return only the case window's size; its coordinates are never reused."""
    source = _source(profile)
    raw = source.get("window", source.get("source_window"))
    if raw is None:
        raw = region.get("window", region.get("source_window"))
    if (
        isinstance(raw, Sequence)
        and not isinstance(raw, (str, bytes))
        and len(raw) == 6
        and all(type(x) is int for x in raw)
    ):
        z0, z1, r0, r1, c0, c1 = raw
        size = (z1 - z0, r1 - r0, c1 - c0)
        if all(item > 0 for item in size):
            return size
    extent = region.get("extent_mm", source.get("extent_mm"))
    if isinstance(extent, Mapping):
        values = (extent.get("z"), extent.get("row"), extent.get("column"))
    elif (
        isinstance(extent, Sequence)
        and not isinstance(extent, (str, bytes))
        and len(extent) == 3
    ):
        values = tuple(extent)
    else:
        return None
    if all(isinstance(item, (int, float)) and item > 0 for item in values):
        tile_mm = source.get("tile_mm", 10.0)
        if not isinstance(tile_mm, (int, float)) or tile_mm <= 0:
            tile_mm = 10.0
        return (
            max(1, round(float(values[0]))),
            max(1, int(float(values[1]) / tile_mm + 0.999999)),
            max(1, int(float(values[2]) / tile_mm + 0.999999)),
        )
    return None


def _profile_exemplars(
    cases: Sequence[Any], subject: str
) -> list[tuple[object, Mapping[str, Any]]]:
    examples: list[tuple[object, Mapping[str, Any]]] = []
    for case in cases:
        if not isinstance(case, Mapping) or case.get("subject") != subject:
            continue
        profile = case.get("profile")
        if _banks(profile) is None:
            continue
        regions = _case_regions(case, subject)
        if not regions:
            regions = [{}]
        for region in regions:
            examples.append((profile, region))
    return examples


def _location_scope(
    cases: Sequence[Any], subject: str, view: tuple[str, str, str] | None
) -> tuple[list[Mapping[str, Any]], list[tuple[object, Mapping[str, Any]]], str]:
    """Choose location precedents by retained scope, keeping legacy rows explicit."""
    if view is None:
        return (
            [
                case
                for case in cases
                if isinstance(case, Mapping)
                and case.get("subject") == subject
                and _banks(case.get("profile")) is not None
            ],
            _profile_exemplars(cases, subject),
            "view_unspecified_compatibility",
        )

    native: list[tuple[Mapping[str, Any], Mapping[str, Any]]] = []
    markers: list[tuple[Mapping[str, Any], Mapping[str, Any]]] = []
    legacy: list[tuple[Mapping[str, Any], Mapping[str, Any]]] = []
    for case in cases:
        if (
            not isinstance(case, Mapping)
            or case.get("subject") != subject
            or _banks(case.get("profile")) is None
        ):
            continue
        regions = _case_regions(case, subject)
        if not regions:
            legacy.append((case, {}))
            continue
        for region in regions:
            if _view_key(region.get("view")) != view:
                continue
            extent = region.get("extent_source")
            if extent == "retained_object_support":
                native.append((case, region))
            elif extent == "retained_physical_location":
                markers.append((case, region))
            elif extent is None:
                legacy.append((case, region))

    selected = native or markers or legacy
    source = (
        "native_object_support"
        if native
        else "retained_physical_location_marker"
        if markers
        else "legacy_unspecified_scope"
    )
    by_case: dict[str, Mapping[str, Any]] = {}
    for case, _region in selected:
        case_id = case.get("case_id")
        identity = case_id if isinstance(case_id, str) else f"object:{id(case)}"
        by_case[identity] = case
    examples = [
        (case.get("profile"), region)
        for case, region in selected
        if _banks(case.get("profile")) is not None
    ]
    if not examples and by_case:
        examples = [(case.get("profile"), {}) for case in by_case.values()]
    return list(by_case.values()), examples, source


def _anchor_names(subject: str, known: set[str]) -> tuple[str, ...]:
    bone_names = {"femur", "tibia", "patella", "fibula"}
    try:
        from knee.collapse.anatomical_relations import RELATIONSHIPS
    except ImportError:
        return ()
    for relation_subject, _predicate, targets, _qualifier, _source in RELATIONSHIPS:
        if (
            relation_subject == subject
            and len(targets) >= 1
            and set(targets).issubset(bone_names | known)
        ):
            bones = tuple(
                name for name in targets if name in bone_names and name in known
            )
            if bones:
                return bones
    return ()


def _object_order(
    known: Sequence[str], priorities: Sequence[Any], anchor_names: set[str]
) -> list[str]:
    rank = {
        name: index for index, name in enumerate(priorities) if isinstance(name, str)
    }
    primary = {"femur", "tibia"}
    dependent_bones = {"fibula", "patella"}
    return sorted(
        known,
        key=lambda name: (
            0 if name in primary else 1 if name in dependent_bones else 2,
            0 if name in anchor_names else 1,
            rank.get(name, len(rank)),
            name,
        ),
    )


def _leg_bounds(
    stack: object,
    leg_map: object = None,
) -> tuple[tuple[int, int, int], tuple[int, int, int], np.ndarray]:
    """Bounds and candidate eligibility from the one shared leg map.

    Only tiles the map calls outside the leg are excluded (Rohan, 2026-10-18:
    what is not in the leg is never computed on). Inside, mixed and unknown
    tiles stay eligible: unknown is never outside, and a missing split must
    not silently stop location on a series. Without a map (a record with no
    native pixels to measure a split from) every covered tile stays eligible.
    """
    from knee.diagnosis.squint_interfaces import LEG_OUTSIDE, leg_map_code

    coverage = getattr(stack, "coverage", None)
    if not isinstance(coverage, np.ndarray) or coverage.ndim != 3:
        raise ValueError("leg_stack_coverage_invalid")
    foreground = np.isfinite(coverage) & (coverage > 0)
    if leg_map is not None:
        if not isinstance(leg_map, Mapping):
            raise TypeError("leg_map_invalid")
        code = leg_map_code(leg_map, grid_shape=coverage.shape)
        if code != "valid":
            raise ValueError(code)
        if leg_map["series_uid"] != getattr(stack, "series_uid", None):
            raise ValueError("leg_map_series_mismatch")
        foreground = foreground & (leg_map["codes"] != LEG_OUTSIDE)
    points = np.argwhere(foreground)
    if not len(points):
        return (0, 0, 0), (0, 0, 0), foreground
    lower = tuple(int(value) for value in points.min(axis=0))
    upper = tuple(int(value) + 1 for value in points.max(axis=0))
    return lower, upper, foreground


_COARSE_METRICS = (
    ("signal_median", "overview"),
    ("signal_minimum", "overview"),
    ("signal_maximum", "overview"),
    ("local_range", "overview"),
    ("gradient_row", "row"),
    ("gradient_column", "column"),
)


def _coarse_index(series: Mapping[str, Any]) -> tuple[list[str], dict[str, np.ndarray]]:
    """Build shared integral histograms for the writer's cached ternary grids."""
    view = series.get("view")
    codes = series.get("metric_codes")
    stack = series.get("stack")
    if not isinstance(view, Mapping) or not isinstance(codes, Mapping):
        return [], {}
    try:
        view_name = json.dumps(
            [
                view[key]
                for key in ("orientation", "fluid_sensitive", "fat_suppression")
            ],
            ensure_ascii=False,
            separators=(",", ":"),
        )
        scale = float(stack.tile_mm)
    except (KeyError, TypeError, ValueError, AttributeError):
        return [], {}
    names: list[str] = []
    integrals: dict[str, np.ndarray] = {}
    for metric, direction in _COARSE_METRICS:
        code_array = codes.get(metric)
        if not isinstance(code_array, np.ndarray) or code_array.ndim != 3:
            continue
        bank = (
            f"squint/v1/view={view_name}/metric={metric}/direction={direction}/"
            f"scale={scale:g}mm"
        )
        names.append(bank)
        for digit in (-1, 0, 1):
            indicator = np.pad(
                np.asarray(code_array == digit, dtype=np.int64),
                ((1, 0), (1, 0), (1, 0)),
            )
            integral = indicator.cumsum(0).cumsum(1).cumsum(2)
            integral = integral.astype(np.int32, copy=False)
            integral.flags.writeable = False
            integrals[f"{bank}\0{digit}"] = integral
    return names, integrals


def _window_coarse_counts(
    names: Sequence[str], integrals: Mapping[str, np.ndarray], window: tuple[int, ...]
) -> tuple[np.ndarray, np.ndarray]:
    """Return exact ternary counts and which overview banks speak in a window."""
    vector = np.zeros((len(names), 3), dtype=np.int64)
    available = np.zeros(len(names), dtype=np.bool_)
    z0, z1, r0, r1, c0, c1 = window
    for index, bank in enumerate(names):
        for digit_index, digit in enumerate((-1, 0, 1)):
            integral = integrals.get(f"{bank}\0{digit}")
            if integral is None:
                continue
            count = (
                integral[z1, r1, c1]
                - integral[z0, r1, c1]
                - integral[z1, r0, c1]
                - integral[z1, r1, c0]
                + integral[z0, r0, c1]
                + integral[z0, r1, c0]
                + integral[z1, r0, c0]
                - integral[z0, r0, c0]
            )
            vector[index, digit_index] = count
        available[index] = bool(vector[index].sum())
    return vector, available


def _window_coarse_batch(
    names: Sequence[str],
    integrals: Mapping[str, np.ndarray],
    windows: Sequence[tuple[int, ...]],
) -> tuple[np.ndarray, np.ndarray]:
    """Compute cached integral counts for a batch of candidate windows."""
    bounds = np.asarray(windows, dtype=np.intp)
    vectors = np.zeros((len(windows), len(names), 3), dtype=np.int64)
    available = np.zeros((len(windows), len(names)), dtype=np.bool_)
    if not names or not windows:
        return vectors, available
    z0, z1, r0, r1, c0, c1 = bounds.T
    for bank_index, bank in enumerate(names):
        for digit_index, digit in enumerate((-1, 0, 1)):
            integral = integrals.get(f"{bank}\0{digit}")
            if integral is None:
                continue
            values = (
                integral[z1, r1, c1]
                - integral[z0, r1, c1]
                - integral[z1, r0, c1]
                - integral[z1, r1, c0]
                + integral[z0, r0, c1]
                + integral[z0, r1, c0]
                + integral[z1, r0, c0]
                - integral[z0, r0, c0]
            )
            vectors[:, bank_index, digit_index] = values
        available[:, bank_index] = vectors[:, bank_index].any(axis=1)
    return vectors, available


def _case_coarse_matrix(
    precedents: Sequence[Mapping[str, Any]],
    names: Sequence[str],
    prevalidated_banks: Sequence[Mapping[str, Sequence[int]] | None] | None = None,
) -> tuple[np.ndarray, np.ndarray]:
    rows = np.zeros((len(precedents), len(names), 3), dtype=np.int64)
    bank_mask = np.zeros((len(precedents), len(names)), dtype=np.bool_)
    for case_index, case in enumerate(precedents):
        banks = (
            prevalidated_banks[case_index]
            if prevalidated_banks is not None
            else _banks(case.get("profile"))
        ) or {}
        for bank_index, name in enumerate(names):
            counts = banks.get(name)
            if counts is not None and len(counts) == 3 and any(counts):
                rows[case_index, bank_index] = counts
                bank_mask[case_index, bank_index] = True
    flat = rows.reshape(len(precedents), len(names) * 3)
    return flat, bank_mask


def _coarse_case_scores(
    vector: np.ndarray,
    vector_banks: np.ndarray,
    case_vectors: np.ndarray,
    case_banks: np.ndarray,
) -> list[tuple[int, int] | None]:
    shared = case_banks & vector_banks[None, :]
    flat_mask = np.repeat(shared, 3, axis=1)
    left = np.where(flat_mask, case_vectors, 0)
    right = np.where(flat_mask, np.broadcast_to(vector.reshape(1, -1), left.shape), 0)
    dots = np.sum(left * right, axis=1, dtype=np.int64)
    left_norms = np.sum(left * left, axis=1, dtype=np.int64)
    right_norms = np.sum(right * right, axis=1, dtype=np.int64)
    output: list[tuple[int, int] | None] = []
    for index, (dot, left_norm, right_norm) in enumerate(
        zip(dots, left_norms, right_norms, strict=True)
    ):
        if not shared[index].any() or not left_norm or not right_norm:
            output.append(None)
        else:
            output.append((int(dot * dot), int(left_norm * right_norm)))
    return output


def _coarse_case_scores_batch(
    vectors: np.ndarray,
    vector_banks: np.ndarray,
    case_vectors: np.ndarray,
    case_banks: np.ndarray,
) -> list[list[tuple[int, int] | None]]:
    """Compute exact coarse cosine fractions for windows against all cases."""
    window_count, bank_count, _ = vectors.shape
    case_count = len(case_vectors)
    if not window_count or not case_count:
        return [[] for _ in range(window_count)]
    case_counts = case_vectors.reshape(case_count, bank_count, 3)
    maximum = max(
        int(vectors.max(initial=0)),
        int(case_counts.max(initial=0)),
    )
    dimensions = max(1, bank_count * 3)
    safe = maximum == 0 or maximum <= math.isqrt(_INT64_MAX // dimensions)
    dtype = np.int64 if safe else object
    left_values = vectors.astype(dtype, copy=False)
    right_values = case_counts.astype(dtype, copy=False)
    shared = vector_banks[:, None, :] & case_banks[None, :, :]
    flat_shared = np.repeat(shared, 3, axis=2)
    left = np.where(flat_shared, left_values.reshape(window_count, 1, -1), 0)
    right = np.where(flat_shared, right_values.reshape(1, case_count, -1), 0)
    dots = np.sum(left * right, axis=2, dtype=dtype)
    left_norms = np.sum(left * left, axis=2, dtype=dtype)
    right_norms = np.sum(right * right, axis=2, dtype=dtype)
    output: list[list[tuple[int, int] | None]] = []
    for window_index in range(window_count):
        row: list[tuple[int, int] | None] = []
        for case_index in range(case_count):
            if not shared[window_index, case_index].any():
                row.append(None)
                continue
            dot = int(dots[window_index, case_index])
            left_sq = int(left_norms[window_index, case_index])
            right_sq = int(right_norms[window_index, case_index])
            row.append(
                (dot * dot, left_sq * right_sq) if left_sq and right_sq else None
            )
        output.append(row)
    return output


def _window_starts(length: int, extent: int) -> range:
    return range(max(1, length - extent + 1))


def _intern_candidate_profiles(
    candidate_profiles: list[dict[str, Any]],
    case_best_candidates: list[dict[str, Any]],
) -> dict[str, dict[str, Any]]:
    """Intern candidate profiles while sharing bank and series-context payloads."""
    catalogs: dict[str, dict[str, Any]] = {
        "profiles": {},
        "banks": {},
        "series_contexts": {},
    }
    canonical_refs: dict[str, dict[str, str]] = {name: {} for name in catalogs}
    ref_contents: dict[str, dict[str, str]] = {name: {} for name in catalogs}
    identity_refs: dict[str, dict[int, str]] = {name: {} for name in catalogs}
    identity_objects: dict[str, dict[int, Any]] = {name: {} for name in catalogs}

    def intern(kind: str, payload: Any, prefix: str) -> str:
        identity = id(payload)
        cached = identity_refs[kind].get(identity)
        if cached is not None and identity_objects[kind][identity] is payload:
            return cached
        canonical = json.dumps(
            payload,
            sort_keys=True,
            ensure_ascii=False,
            separators=(",", ":"),
            allow_nan=False,
        )
        cached = canonical_refs[kind].get(canonical)
        if cached is None:
            digest = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
            ref = f"{prefix}-{digest}"
            suffix = 0
            while ref in ref_contents[kind] and ref_contents[kind][ref] != canonical:
                suffix += 1
                ref = f"{prefix}-{digest}-{suffix}"
            cached = ref
            canonical_refs[kind][canonical] = ref
            ref_contents[kind][ref] = canonical
            catalogs[kind][ref] = payload
        identity_refs[kind][identity] = cached
        identity_objects[kind][identity] = payload
        return cached

    public_object = {
        "evidence": {
            "candidate_profile_catalog": catalogs["profiles"],
            "candidate_bank_catalog": catalogs["banks"],
            "candidate_series_context_catalog": catalogs["series_contexts"],
        }
    }
    profile_identity_refs: dict[int, str] = {}
    profile_identity_objects: dict[int, Any] = {}

    def reference(profile: Any) -> str:
        if profile is None:
            ref = "profile-unavailable"
            catalogs["profiles"].setdefault(
                ref,
                {"schema": "knee.squint-candidate-profile/v2", "status": "unavailable"},
            )
            return ref
        identity = id(profile)
        cached = profile_identity_refs.get(identity)
        if cached is not None and profile_identity_objects[identity] is profile:
            return cached
        if not isinstance(profile, Mapping):
            raise TypeError("candidate_profile_must_be_mapping")
        fields = {
            key: value
            for key, value in profile.items()
            if key not in ("banks", "source")
        }
        raw_banks = profile.get("banks")
        if not isinstance(raw_banks, Mapping):
            raise TypeError("candidate_profile_banks_must_be_mapping")
        bank_ref = intern("banks", raw_banks, "banks")
        source_present = "source" in profile
        source = profile.get("source", {})
        source_is_mapping = isinstance(source, Mapping)
        source_fields = dict(source) if source_is_mapping else source
        context_present = source_is_mapping and "series_context" in source
        context_ref = (
            intern("series_contexts", source["series_context"], "series-context")
            if context_present
            else None
        )
        if source_is_mapping and context_present:
            source_fields = {
                key: value for key, value in source.items() if key != "series_context"
            }
        factored = {
            "schema": "knee.squint-candidate-profile/v2",
            "status": "available",
            "profile_fields": fields,
            "banks_ref": bank_ref,
            "source_present": source_present,
            "source_is_mapping": source_is_mapping,
            "source_fields": source_fields,
            "source_has_series_context": context_present,
            "series_context_ref": context_ref,
        }
        cached = intern("profiles", factored, "profile")
        if resolve_candidate_profile(public_object, cached) != profile:
            raise ValueError("candidate_profile_publication_readback_mismatch")
        profile_identity_refs[identity] = cached
        profile_identity_objects[identity] = profile
        return cached

    for candidate in candidate_profiles:
        candidate["profile_ref"] = reference(candidate.pop("profile", None))
    for case in case_best_candidates:
        for candidate in case.get("candidates", ()):
            candidate["profile_ref"] = reference(candidate.pop("profile", None))
    return {name: dict(sorted(values.items())) for name, values in catalogs.items()}


def resolve_candidate_profile(
    located_object: Mapping[str, Any], profile_ref: str
) -> Any:
    """Reconstruct a complete candidate profile from its factored catalogs."""
    if not isinstance(located_object, Mapping):
        raise TypeError("candidate_profile_object_must_be_mapping")
    evidence = located_object.get("evidence")
    if not isinstance(evidence, Mapping):
        raise TypeError("candidate_profile_evidence_missing")
    if not isinstance(profile_ref, str) or not profile_ref:
        raise ValueError("candidate_profile_ref_invalid")
    profiles = evidence.get("candidate_profile_catalog")
    banks = evidence.get("candidate_bank_catalog")
    contexts = evidence.get("candidate_series_context_catalog")
    if not isinstance(profiles, Mapping) or profile_ref not in profiles:
        raise ValueError("candidate_profile_ref_missing")
    entry = profiles[profile_ref]
    if not isinstance(entry, Mapping):
        raise TypeError("candidate_profile_entry_invalid")
    if entry.get("schema") != "knee.squint-candidate-profile/v2":
        raise ValueError("candidate_profile_schema_invalid")
    if entry.get("status") == "unavailable":
        return None
    if entry.get("status") != "available":
        raise ValueError("candidate_profile_status_invalid")
    bank_ref = entry.get("banks_ref")
    if (
        not isinstance(banks, Mapping)
        or not isinstance(bank_ref, str)
        or bank_ref not in banks
    ):
        raise ValueError("candidate_profile_banks_ref_missing")
    fields = entry.get("profile_fields")
    if not isinstance(fields, Mapping):
        raise TypeError("candidate_profile_fields_invalid")
    result = dict(fields)
    result["banks"] = banks[bank_ref]
    if entry.get("source_present") is not True:
        if (
            entry.get("source_has_series_context")
            or entry.get("series_context_ref") is not None
        ):
            raise ValueError("candidate_profile_absent_source_has_context")
    elif entry.get("source_is_mapping") is True:
        source_fields = entry.get("source_fields")
        if not isinstance(source_fields, Mapping):
            raise ValueError("candidate_profile_source_fields_invalid")
        source = dict(source_fields)
        if entry.get("source_has_series_context") is True:
            context_ref = entry.get("series_context_ref")
            if (
                not isinstance(contexts, Mapping)
                or not isinstance(context_ref, str)
                or context_ref not in contexts
            ):
                raise ValueError("candidate_profile_series_context_ref_missing")
            source["series_context"] = contexts[context_ref]
        elif entry.get("series_context_ref") is not None:
            raise ValueError("candidate_profile_series_context_ref_unexpected")
        result["source"] = source
    elif entry.get("source_is_mapping") is False:
        if (
            entry.get("source_has_series_context")
            or entry.get("series_context_ref") is not None
        ):
            raise ValueError("candidate_profile_nonmapping_source_has_context")
        result["source"] = entry.get("source_fields")
    else:
        raise ValueError("candidate_profile_source_kind_invalid")
    return result


def locate_objects(study: dict, memory: dict, deadline: float | None = None) -> dict:
    """Use anatomy-first finite windows for raw studies, cached profiles otherwise."""
    if not isinstance(study, dict) or not isinstance(memory, dict):
        return {
            "outcome": "invalid_input",
            "reason": "study_and_memory_must_be_objects",
            "objects": {},
        }
    series, _uids = _profile_candidates(study)
    raw_stack_present = any(
        getattr(row.get("stack"), "code", None) == "present"
        and isinstance(getattr(row.get("stack"), "median", None), np.ndarray)
        for row in series
    )
    if raw_stack_present:
        from knee.diagnosis.squint_anatomy_locator import locate_anatomy_first
        from knee.diagnosis.squint_leg import leg_maps

        # The territory writer may already have made these. Share that exact
        # result rather than measuring the background split a second time.
        maps = study.get("leg_maps")
        leg_status = "shared"
        if maps is None:
            try:
                maps = leg_maps(study)
                leg_status = "measured"
            except (TypeError, ValueError) as error:
                # Records without native pixels (no split can be measured):
                # every covered tile stays eligible, and the reason is kept.
                maps, leg_status = {}, f"unavailable:{error}"
        located_study = {
            **study,
            "leg_maps": maps,
            "leg_map_status": leg_status,
            "series": [
                {**row, "leg_map": maps.get(row.get("series_uid"))} for row in series
            ],
        }
        return locate_anatomy_first(located_study, memory, deadline)
    return _locate_cached_objects(study, memory, deadline)


def recall_object(
    profile: dict,
    memory: dict,
    question: str,
    exclude_study_uid: str = "",
    *,
    selection: Any = _UNSELECTED,
) -> dict:
    """Compare every eligible individual precedent and retain conflict/proposals."""
    question_id = _question_id(question)
    if (
        not isinstance(profile, Mapping)
        or not isinstance(memory, dict)
        or question_id is None
    ):
        return {
            "outcome": "invalid_input",
            "reason": "profile_memory_and_question_required",
            "case_terms": [],
            "censor_terms": [],
            "speaking_calls": [],
        }
    if not isinstance(exclude_study_uid, str):
        return {
            "outcome": "invalid_input",
            "reason": "invalid_study_exclusion",
            "case_terms": [],
            "censor_terms": [],
            "speaking_calls": [],
        }
    cases = memory.get("cases")
    if not isinstance(cases, Sequence) or isinstance(cases, (str, bytes)):
        return {
            "outcome": "invalid_input",
            "reason": "memory_cases_required",
            "case_terms": [],
            "censor_terms": [],
            "speaking_calls": [],
        }
    subject = _subject(profile)
    query_banks = profile.get("banks")
    if subject is None or not isinstance(query_banks, Mapping):
        return {
            "outcome": "invalid_input",
            "reason": "invalid_profile",
            "question_id": question_id,
            "case_terms": [],
            "censor_terms": [],
            "speaking_calls": [],
        }
    prepared = memory.get("prepared_recall")
    if selection is _UNSELECTED:
        selection = memory.get("recall_selection", _UNSELECTED)
    if (
        selection is _UNSELECTED
        and isinstance(prepared, Mapping)
        and "selections" in prepared
    ):
        selection = prepared["selections"].get(question_id)
    refusal = {
        "outcome": "proposal",
        "question_id": question_id,
        "subject": subject,
        "case_terms": [],
        "censor_terms": [],
        "speaking_calls": [],
        "vetoed_answers": [],
    }
    if selection is _UNSELECTED:
        from knee.diagnosis.squint_interfaces import TERRITORY_PROCEDURE

        if _source(profile).get("procedure") == TERRITORY_PROCEDURE:
            try:
                from knee.diagnosis.squint_questions import question_selection

                selection = question_selection(question_id)
            except ImportError:
                return {**refusal, "reason": "question_selector_unavailable"}
            except ValueError as error:
                return {**refusal, "reason": str(error)}
    selected = selection is not _UNSELECTED
    if selected:
        from knee.diagnosis.squint_interfaces import selection_code

        code = selection_code(selection)
        if code != "valid":
            return {**refusal, "reason": code}
        if selection["question_id"] != question_id:
            return {**refusal, "reason": "selection_question_mismatch"}
        if not selection["cheap"]:
            return {**refusal, "reason": "selection_empty"}
        if selection.get(
            "cheap_procedure", _source(profile).get("procedure")
        ) != _source(profile).get("procedure"):
            return {**refusal, "reason": "selection_procedure_mismatch"}
        try:
            query_banks = _selected_profile_banks(selection, subject, profile)
            names = tuple(query_banks) if query_banks is not None else ()
            digest = _selection_digest(selection)
        except ImportError:
            return {**refusal, "reason": "question_selector_unavailable"}
        except (TypeError, ValueError):
            return {**refusal, "reason": "selection_descriptor_invalid"}
        if query_banks is None:
            return {**refusal, "outcome": "invalid_input", "reason": "invalid_profile"}
        if not names:
            return {**refusal, "reason": "selection_no_compatible_banks"}
        identities = (
            prepared.get("selection_identity", {})
            if isinstance(prepared, Mapping)
            else {}
        )
        identity = (
            identities.get(question_id) if isinstance(identities, Mapping) else None
        )
        if not isinstance(identity, Mapping) or not isinstance(
            identity.get("selected_banks"), Mapping
        ):
            return {
                **refusal,
                "reason": "recall_preparation_selection_identity_missing",
            }
        if (
            identity.get("version") != selection["version"]
            or identity.get("descriptor_sha256") != digest
        ):
            return {
                **refusal,
                "reason": "recall_preparation_selection_identity_mismatch",
            }
    else:
        query_banks = _banks(profile)
        if query_banks is None:
            return {**refusal, "outcome": "invalid_input", "reason": "invalid_profile"}
    if (
        not isinstance(prepared, Mapping)
        or prepared.get("schema") != "knee.squint-recall-preparation/v1"
    ):
        return {
            "outcome": "proposal",
            "reason": "recall_preparation_required",
            "question_id": question_id,
            "subject": subject,
            "case_terms": [],
            "censor_terms": [],
            "speaking_calls": [],
            "vetoed_answers": [],
        }
    envelopes = prepared.get("envelopes", {}) if isinstance(prepared, Mapping) else {}
    subject_envelopes = (
        envelopes.get(subject, {}) if isinstance(envelopes, Mapping) else {}
    )
    question_envelopes = (
        subject_envelopes.get(question_id, {})
        if isinstance(subject_envelopes, Mapping)
        else {}
    )
    case_indices = prepared.get("case_indices", {})
    subject_case_indices = (
        case_indices.get(subject, {}) if isinstance(case_indices, Mapping) else {}
    )
    selected_indices = (
        subject_case_indices.get(question_id, ())
        if isinstance(subject_case_indices, Mapping)
        else ()
    )
    if not isinstance(selected_indices, Sequence):
        selected_indices = ()
    base: dict[str, Any] = {
        "question_id": question_id,
        "subject": subject,
        "outcome": "proposal",
        "case_terms": [],
        "case_reasons": [],
        "censor_terms": [],
        "speaking_calls": [],
        "speaking_case_ids": [],
        "excluded_case_ids": [],
        "incompatible_case_ids": [],
        "silent_case_ids": [],
        "nearest_positive_case_ids": [],
        "nearest_negative_case_ids": [],
        "vetoed_answers": [],
        "source": {
            "memory": memory.get("source", memory.get("metadata", {})),
            "envelopes_used": [],
        },
    }
    if selected:
        base["source"]["selection"] = {
            "schema": selection["schema"],
            "version": selection["version"],
            "descriptor_sha256": digest,
            "selected_banks": list(names),
            "subjects": dict(selection["subjects"]),
        }
    if not isinstance(question_envelopes, Mapping):
        question_envelopes = {}
    if not question_envelopes:
        base["envelope_status"] = "unavailable_proposal_only"
    records: list[tuple[int, tuple[int, int], dict[str, Any]]] = []
    case_profile_banks = (
        prepared.get("question_case_profile_banks", {}).get(question_id, {})
        if selected
        else prepared.get("case_profile_banks", {})
    )
    if not isinstance(case_profile_banks, Mapping):
        case_profile_banks = {}
    selected_cases: list[
        tuple[int, Mapping[str, Any], int, Mapping[str, Sequence[int]] | None]
    ] = []
    for case_index in selected_indices:
        if type(case_index) is not int or not 0 <= case_index < len(cases):
            continue
        case = cases[case_index]
        if not isinstance(case, Mapping):
            continue
        sign = _call(case, question_id)
        if sign not in (-1, 1) or case.get("subject") != subject:
            continue
        case_id = case.get("case_id")
        study_uid = case.get("study_uid")
        if (
            isinstance(exclude_study_uid, str)
            and exclude_study_uid
            and study_uid == exclude_study_uid
        ):
            if isinstance(case_id, str):
                base["excluded_case_ids"].append(case_id)
                base["case_reasons"].append(
                    {"case_id": case_id, "reason_code": "excluded_same_study"}
                )
            continue
        banks = case_profile_banks.get(case_index)
        if banks is None:
            banks = (
                _selected_profile_banks(selection, subject, case.get("profile"))
                if selected
                else _banks(case.get("profile"))
            )
        selected_cases.append((case_index, case, sign, banks))
    aligned_banks = [banks for _case_index, _case, _sign, banks in selected_cases]
    query_procedure = _source(profile).get("procedure")
    procedure_compatibility = [
        query_procedure == _source(case.get("profile")).get("procedure")
        for _case_index, case, _sign, _banks_value in selected_cases
    ]
    subject_matrices = (
        prepared.get("question_profile_matrices", {})
        if selected
        else prepared.get("subject_profile_matrices", {})
    )
    matrix_cache = (
        subject_matrices.get(subject) if isinstance(subject_matrices, Mapping) else None
    )
    if selected and isinstance(matrix_cache, Mapping):
        matrix_cache = matrix_cache.get(question_id)
    batched_evidence = _batch_terms(
        query_banks,
        aligned_banks,
        matrix_cache=matrix_cache if isinstance(matrix_cache, Mapping) else None,
        compatible=procedure_compatibility,
        row_indices=[
            case_index for case_index, _case, _sign, _banks_value in selected_cases
        ]
        if isinstance(matrix_cache, Mapping)
        else None,
    )
    for (_case_index, case, sign, banks), evidence in zip(
        selected_cases, batched_evidence, strict=True
    ):
        case_id = case.get("case_id")
        study_uid = case.get("study_uid")
        if (
            banks is None
            or not _same_procedure(profile, case.get("profile"))
            or evidence is None
        ):
            if isinstance(case_id, str):
                base["incompatible_case_ids"].append(case_id)
                base["case_reasons"].append(
                    {"case_id": case_id, "reason_code": "incompatible_encoding"}
                )
            continue
        if evidence.get("code") == "silent":
            if isinstance(case_id, str):
                base["silent_case_ids"].append(case_id)
                base["case_reasons"].append(
                    {
                        "case_id": case_id,
                        "reason_code": "no_common_selected_reading"
                        if selected
                        else "no_common_reading",
                    }
                )
            continue
        ratio = evidence["cosine_squared"]
        bank_key = json.dumps(
            tuple(evidence["common_speaking_banks"]), separators=(",", ":")
        )
        envelope = question_envelopes.get(bank_key)
        maximum = None
        if isinstance(envelope, Mapping) and envelope.get("available"):
            raw = envelope.get("maximum_squared_cosine")
            try:
                maximum = (
                    (int(raw["numerator"]), int(raw["denominator"]))
                    if isinstance(raw, Mapping)
                    else None
                )
            except (KeyError, TypeError, ValueError):
                maximum = None
        reaches = maximum is not None and ratio[0] * maximum[1] > maximum[0] * ratio[1]
        if maximum is None:
            base["envelope_status"] = "unavailable_proposal_only"
        envelope_ref = {
            "source": envelope.get("source")
            if isinstance(envelope, Mapping)
            else "unavailable",
            "question": question_id,
            "subject": subject,
            "banks": evidence["common_speaking_banks"],
            "independent_comparison_count": envelope.get(
                "independent_comparison_count", 0
            )
            if isinstance(envelope, Mapping)
            else 0,
        }
        if envelope_ref not in base["source"]["envelopes_used"]:
            base["source"]["envelopes_used"].append(envelope_ref)
        record = {
            "case_id": case_id,
            "study_uid": study_uid,
            "call": sign,
            "call_scope": _case_call_scope(case, question_id),
            "terms": {
                key: evidence[key] for key in ("dot", "left_norm_sq", "right_norm_sq")
            },
            "common_speaking_banks": evidence["common_speaking_banks"],
            "squared_cosine": {
                "numerator": str(ratio[0]),
                "denominator": str(ratio[1]),
            },
            "reaches_empirical_envelope": reaches,
            "reason_code": "no_compatible_envelope"
            if maximum is None
            else "above_empirical_envelope"
            if reaches
            else "below_empirical_envelope",
            "trust": None
            if maximum is None
            else {
                "numerator": str(maximum[0]),
                "denominator": str(maximum[1]),
                "source": envelope_ref["source"],
                "comparison_kind": "strict_squared_cosine_above_finite_empirical_opposition_floor",
            },
            "reaches_trust": reaches,
            "source": case.get("teaching_source", case.get("source")),
        }
        records.append((sign, ratio, record))
        base["case_terms"].append(record)
        base["case_reasons"].append(
            {"case_id": case_id, "reason_code": record["reason_code"]}
        )
        if reaches:
            base["speaking_calls"].append(sign)
            if isinstance(case_id, str):
                base["speaking_case_ids"].append(case_id)
    for sign, target in (
        (1, "nearest_positive_case_ids"),
        (-1, "nearest_negative_case_ids"),
    ):
        candidates = [row for row in records if row[0] == sign]
        if candidates:
            best = candidates[0][1]
            for _, ratio, _ in candidates[1:]:
                if ratio[0] * best[1] > best[0] * ratio[1]:
                    best = ratio
            base[target] = [
                row[2]["case_id"]
                for row in candidates
                if row[1][0] * best[1] == best[0] * row[1][1]
            ]
    censors = memory.get("censors", ())
    censor_indices = prepared.get("censor_indices", {})
    selected_censor_indices = (
        censor_indices.get(question_id, ())
        if isinstance(censor_indices, Mapping)
        else ()
    )
    vetoed: set[int] = set()
    if isinstance(censors, Sequence) and not isinstance(censors, (str, bytes)):
        for censor_index in selected_censor_indices:
            if type(censor_index) is not int or not 0 <= censor_index < len(censors):
                continue
            censor = censors[censor_index]
            if (
                not isinstance(censor, Mapping)
                or censor.get("question", censor.get("condition")) != question_id
            ):
                continue
            answer = censor.get("answer")
            if type(answer) is not int or answer not in (-1, 1):
                continue
            censor_profile = censor.get("profile")
            if selected:
                censor_banks = _selected_profile_banks(
                    selection, subject, censor_profile
                )
                if (
                    censor_banks is None
                    or _subject(censor_profile) != subject
                    or not _same_procedure(profile, censor_profile)
                ):
                    continue
                evidence = _exact_bank_terms(query_banks, censor_banks)
            else:
                evidence = _terms(profile, censor_profile)
            if evidence is None or evidence["code"] != "ok":
                continue
            numerator, denominator = (
                censor.get("radius_numerator"),
                censor.get("radius_denominator"),
            )
            reaches = (
                type(numerator) is int
                and type(denominator) is int
                and denominator > 0
                and numerator >= 0
                and numerator <= denominator
                and denominator * denominator * evidence["dot"] * evidence["dot"]
                >= numerator
                * numerator
                * evidence["left_norm_sq"]
                * evidence["right_norm_sq"]
            )
            row = {
                "censor_id": censor.get("censor_id"),
                "answer": answer,
                "source": censor.get("source"),
                "terms": {
                    key: evidence[key]
                    for key in ("dot", "left_norm_sq", "right_norm_sq")
                },
                "common_speaking_banks": evidence["common_speaking_banks"],
                "reaches_trust": reaches,
            }
            base["censor_terms"].append(row)
            if reaches:
                vetoed.add(answer)
    base["vetoed_answers"] = sorted(vetoed)
    signs = set(base["speaking_calls"]) - vetoed
    if signs == {1, -1}:
        base["outcome"] = "unresolved_conflict"
    elif signs == {1}:
        base["outcome"] = "present"
    elif signs == {-1}:
        base["outcome"] = "absent"
    elif vetoed:
        base["outcome"] = "unresolved_censored"
    elif base["case_terms"]:
        base["outcome"] = "proposal"
    elif base["incompatible_case_ids"]:
        base["outcome"] = "incompatible_encoding"
    else:
        base["outcome"] = "unresolved_no_precedent"
    # Explicit ordinary negative calls are cases, never censor records.
    return base


def _current_leg_frame_prior(
    series: Sequence[Mapping[str, Any]],
    foreground_by_series: dict[int, np.ndarray] | None = None,
) -> tuple[tuple[float, ...], tuple[float, ...]] | None:
    """Measure finite current-study foreground bounds in LPS once per study."""
    points: list[np.ndarray] = []
    for record in series:
        stack = record.get("stack")
        centres = np.asarray(getattr(stack, "centres_lps", None))
        if centres.ndim != 4 or centres.shape[-1] != 3:
            continue
        if foreground_by_series is not None and id(record) in foreground_by_series:
            foreground = foreground_by_series[id(record)]
        else:
            _lower, _upper, foreground = _leg_bounds(stack, record.get("leg_map"))
        if foreground.shape != centres.shape[:3]:
            continue
        valid = foreground & np.isfinite(centres).all(axis=-1)
        if valid.any():
            points.append(centres[valid])
    if not points:
        return None
    all_points = np.concatenate(points, axis=0)
    low = np.min(all_points, axis=0)
    high = np.max(all_points, axis=0)
    if not np.isfinite(low).all() or not np.isfinite(high).all() or np.any(high < low):
        return None
    return tuple(float(value) for value in low), tuple(float(value) for value in high)


def _anatomical_window_proposal(
    series_record: Mapping[str, Any],
    subject: str,
    *,
    leg_bounds_lps: tuple[tuple[float, ...], tuple[float, ...]] | None,
    foreground: np.ndarray | None = None,
    anchors: Mapping[str, Any],
    knee_side: str | None,
    knee_scale_mm: float | None,
) -> dict[str, Any]:
    """Ask the authored anatomy helper for finite current-study windows only."""
    if leg_bounds_lps is None:
        return {
            "status": "geometry_unavailable",
            "windows": [],
            "reason": "current_leg_bounds_unavailable",
        }
    try:
        from knee.diagnosis.squint_anatomical_priors import anatomical_windows
    except ImportError:
        return {
            "status": "geometry_unavailable",
            "windows": [],
            "reason": "anatomical_prior_helper_unavailable",
        }
    try:
        series_for_helper = dict(series_record)
        if foreground is not None:
            series_for_helper["foreground"] = foreground
        proposal = anatomical_windows(
            series_for_helper,
            subject,
            leg_bounds_lps=leg_bounds_lps,
            anchors=dict(anchors),
            knee_side=knee_side,
            knee_scale_mm=knee_scale_mm,
        )
    except (TypeError, ValueError) as error:
        return {
            "status": "geometry_unavailable",
            "windows": [],
            "reason": f"anatomical_prior_invalid:{type(error).__name__}",
        }
    if not isinstance(proposal, Mapping):
        return {
            "status": "geometry_unavailable",
            "windows": [],
            "reason": "anatomical_prior_result_invalid",
        }
    raw_windows = proposal.get("windows")
    if not isinstance(raw_windows, Sequence) or isinstance(raw_windows, (str, bytes)):
        return {
            "status": "geometry_unavailable",
            "windows": [],
            "reason": "anatomical_prior_windows_invalid",
        }
    stack = series_record.get("stack")
    shape = getattr(getattr(stack, "median", None), "shape", ())
    clean: list[tuple[int, ...]] = []
    for raw in raw_windows:
        if (
            not isinstance(raw, (tuple, list))
            or len(raw) != 6
            or any(type(value) is not int for value in raw)
        ):
            continue
        window = tuple(raw)
        z0, z1, r0, r1, c0, c1 = window
        if len(shape) != 3 or not (
            0 <= z0 < z1 <= shape[0]
            and 0 <= r0 < r1 <= shape[1]
            and 0 <= c0 < c1 <= shape[2]
            and z1 - z0 == 1
        ):
            continue
        clean.append(window)
    result = dict(proposal)
    result["windows"] = sorted(set(clean))
    if not result["windows"] and result.get("status") in {
        "available",
        "proposed",
        "ok",
    }:
        result["status"] = "no_valid_native_window"
    return result


def _window_centre_lps(
    series: Mapping[str, Any], window: tuple[int, ...]
) -> list[float] | None:
    stack = series.get("stack")
    centres = np.asarray(getattr(stack, "centres_lps", None))
    if centres.ndim != 4 or centres.shape[-1] != 3:
        return None
    z0, z1, r0, r1, c0, c1 = window
    selected = centres[z0:z1, r0:r1, c0:c1]
    finite = selected[np.isfinite(selected).all(axis=-1)]
    if not len(finite):
        return None
    return [float(value) for value in np.mean(finite, axis=0)]


def _locate_cached_objects(
    study: dict, memory: dict, deadline: float | None = None
) -> dict:
    """Compare only caller-supplied candidate profiles when no raw stack is present."""
    cases = memory.get("cases", ())
    case_rows = (
        list(cases)
        if isinstance(cases, Sequence) and not isinstance(cases, (str, bytes))
        else []
    )
    known = sorted(
        {
            row.get("subject")
            for row in case_rows
            if isinstance(row, Mapping)
            and isinstance(row.get("subject"), str)
            and not row["subject"].startswith("diagnosis/")
        }
    )
    declared = memory.get("objects", ())
    if isinstance(declared, Sequence) and not isinstance(declared, (str, bytes)):
        known.extend(
            name
            for name in declared
            if isinstance(name, str)
            and not name.startswith("diagnosis/")
            and name not in known
        )
    priorities = memory.get("object_order", ())
    priorities = (
        priorities
        if isinstance(priorities, Sequence) and not isinstance(priorities, (str, bytes))
        else ()
    )
    known = _object_order(known, priorities, {"femur", "tibia", "fibula", "patella"})
    objects = {
        name: {
            "status": "unresolved_missing_reading",
            "profile": None,
            "candidate_profiles": [],
            "regions": [],
            "evidence": {"reason": "no_current_study_candidate_profiles"},
        }
        for name in known
    }
    series, series_uids = _profile_candidates(study)
    series_by_uid = {
        row.get("series_uid"): row
        for row in series
        if isinstance(row.get("series_uid"), str)
    }
    geometry_by_subject: dict[str, dict[str, Any]] = {}
    for subject in known:
        if deadline is not None and time.monotonic() >= deadline:
            objects[subject]["evidence"] = {
                "reason": "deadline_before_search",
                "deadline_reached": True,
            }
            continue
        by_view: dict[tuple[str, str, str] | None, dict[str, Any]] = {}
        case_best: dict[str, dict[str, Any]] = {}
        precedent_scopes: dict[str, dict[str, Any]] = {}
        for series_record in series:
            view = _view_key(series_record.get("view"))
            scoped, _examples, source = _location_scope(case_rows, subject, view)
            scope_key = json.dumps(view, separators=(",", ":"))
            precedent_scopes[scope_key] = {
                "view": None if view is None else list(view),
                "source": source,
                "case_ids": [
                    row.get("case_id")
                    for row in scoped
                    if isinstance(row.get("case_id"), str)
                ],
            }
            compatible = [
                row
                for row in scoped
                if _source(row.get("profile")).get("procedure") is not None
            ]
            candidates = series_record.get("candidate_profiles", ())
            if not isinstance(candidates, Sequence) or isinstance(
                candidates, (str, bytes)
            ):
                continue
            for candidate in candidates:
                if (
                    not isinstance(candidate, Mapping)
                    or candidate.get("subject") != subject
                ):
                    continue
                query = _banks(candidate.get("profile"))
                if query is None:
                    continue
                query_procedure = _source(candidate.get("profile")).get("procedure")
                rows = [
                    row
                    for row in compatible
                    if _source(row.get("profile")).get("procedure") == query_procedure
                ]
                banks = [_banks(row.get("profile")) for row in rows]
                scores = _batch_terms(query, banks, compatible=[True] * len(rows))
                usable = [
                    (row, item)
                    for row, item in zip(rows, scores, strict=True)
                    if item is not None and item.get("code") == "ok"
                ]
                if not usable:
                    continue
                best = usable[0][1]["cosine_squared"]
                for _row, item in usable[1:]:
                    score = item["cosine_squared"]
                    if score[0] * best[1] > best[0] * score[1]:
                        best = score
                for case, item in usable:
                    case_id = case.get("case_id")
                    if not isinstance(case_id, str):
                        continue
                    score = item["cosine_squared"]
                    entry = {
                        "profile": candidate["profile"],
                        "series_uid": series_record.get("series_uid"),
                        "view": series_record.get("view"),
                        "window": candidate.get("window"),
                    }
                    current = case_best.get(case_id)
                    if (
                        current is None
                        or score[0] * current["score"][1]
                        > current["score"][0] * score[1]
                    ):
                        case_best[case_id] = {"score": score, "items": [entry]}
                    elif (
                        score[0] * current["score"][1] == current["score"][0] * score[1]
                    ):
                        current["items"].append(entry)
                group = by_view.get(view)
                if (
                    group is None
                    or best[0] * group["score"][1] > group["score"][0] * best[1]
                ):
                    by_view[view] = {
                        "score": best,
                        "items": [(dict(candidate), series_record)],
                        "source": source,
                    }
                elif best[0] * group["score"][1] == group["score"][0] * best[1]:
                    group["items"].append((dict(candidate), series_record))
        if not by_view:
            continue
        candidate_profiles = []
        regions = []
        chosen = []
        for group in by_view.values():
            for candidate, series_record in group["items"]:
                candidate_profiles.append(
                    {
                        "profile": candidate["profile"],
                        "series_uid": series_record.get("series_uid"),
                        "view": series_record.get("view"),
                        "window": candidate.get("window"),
                        "squared_similarity": {
                            "numerator": str(group["score"][0]),
                            "denominator": str(group["score"][1]),
                        },
                    }
                )
                regions.append(
                    {
                        "series_uid": series_record.get("series_uid"),
                        "view": series_record.get("view"),
                        "window": candidate.get("window")
                        or _source(candidate.get("profile")).get("window"),
                    }
                )
            if len(group["items"]) == 1:
                chosen.append(group["items"][0][0]["profile"])
        merged = chosen[0] if len(chosen) == 1 else None
        best_candidates = [
            {
                "case_id": key,
                "squared_similarity": {
                    "numerator": str(row["score"][0]),
                    "denominator": str(row["score"][1]),
                },
                "candidates": row["items"],
            }
            for key, row in sorted(case_best.items())
        ]
        catalog = _intern_candidate_profiles(candidate_profiles, best_candidates)
        try:
            from knee.diagnosis.squint_geometry import (
                object_geometry,
                relative_scope_priors,
            )

            spatial = object_geometry(subject, regions, series_by_uid)
            geometry_by_subject[subject] = spatial
            relative_priors = relative_scope_priors(
                subject,
                _anchor_names(subject, set(known)),
                case_rows,
                geometry_by_subject,
            )
        except (ImportError, TypeError, ValueError):
            spatial = None
            relative_priors = {
                "schema": "knee.squint-relative-scope-priors/v1",
                "subject": subject,
                "anchors": [],
                "cases": [],
            }
        objects[subject] = {
            "status": "proposal",
            "profile": merged,
            "candidate_profiles": candidate_profiles,
            "regions": regions,
            "evidence": {
                "source": "caller_supplied_candidate_profiles",
                "candidate_view_count": len(by_view),
                "selected_view_regions": len(chosen),
                "candidate_profiles_compared": len(candidate_profiles),
                "location_precedent_scopes": [
                    precedent_scopes[key] for key in sorted(precedent_scopes)
                ],
                "spatial_constraints": spatial,
                "relative_scope_priors": relative_priors,
                "case_best_candidates": best_candidates,
                "candidate_profile_catalog": catalog["profiles"],
                "candidate_bank_catalog": catalog["banks"],
                "candidate_series_context_catalog": catalog["series_contexts"],
                "patient_coordinates_carried": False,
            },
        }
    return {
        "outcome": "located_with_proposals",
        "study_uid": study.get("study_uid"),
        "objects": objects,
        "evidence": {
            "series_uids": series_uids,
            "candidate_generation": "caller_supplied_profiles_only",
        },
    }


_MAX_EXACT_REFINEMENTS_PER_VIEW = 16
