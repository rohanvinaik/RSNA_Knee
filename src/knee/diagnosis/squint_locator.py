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


def _question_id(question: object) -> str | None:
    if isinstance(question, str) and question:
        return question
    if isinstance(question, Mapping):
        value = question.get("question_id", question.get("condition"))
        return value if isinstance(value, str) and value else None
    return None


def prepare_recall(memory: dict) -> dict:
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
    case_banks = _validated_case_banks(cases)
    subject_profile_matrices: dict[str, dict[str, Any]] = {}
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
    pair_cache: dict[tuple[int, int], list[tuple[str, dict[str, Any]]]] = {}

    def pair_projections(
        first_index: int, second_index: int
    ) -> list[tuple[str, dict[str, Any]]]:
        key = (first_index, second_index)
        cached = pair_cache.get(key)
        if cached is not None:
            return cached
        first_banks = case_banks[first_index]
        second_banks = case_banks[second_index]
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
        subject_profile_matrices[subject] = _case_matrix(
            [case_banks.get(index) for index in all_subject_indices],
            all_subject_indices,
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
                    for mode, evidence in pair_projections(first_index, second_index):
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
    return {
        "outcome": "prepared",
        "schema": "knee.squint-recall-preparation/v1",
        "memory_source": memory.get("source", memory.get("metadata", {})),
        "envelopes": envelopes,
        "case_indices": case_indices,
        "censor_indices": censor_indices,
        "case_profile_banks": case_banks,
        "subject_profile_matrices": subject_profile_matrices,
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
) -> tuple[tuple[int, int, int], tuple[int, int, int], np.ndarray]:
    coverage = np.asarray(stack.coverage)
    valid = np.isfinite(coverage) & (coverage > 0)
    maximum = getattr(stack, "maximum", None)
    if (
        isinstance(maximum, np.ndarray)
        and maximum.shape == coverage.shape
        and valid.any()
    ):
        usable = valid & np.isfinite(maximum)
        if usable.any():
            scan_lowest = float(np.min(maximum[usable]))
            foreground = usable & (maximum > scan_lowest)
            if foreground.any():
                valid = foreground
    points = np.argwhere(valid)
    if not len(points):
        return (0, 0, 0), tuple(int(dim) for dim in coverage.shape), valid
    lower = tuple(int(value) for value in points.min(axis=0))
    upper = tuple(int(value) + 1 for value in points.max(axis=0))
    return lower, upper, valid


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
    """Locate case-known objects from current-study squint grids, preserving silence.

    The writer may supply cached candidate profiles in each series record. When
    those are absent, this function reports honest unavailability rather than
    reconstructing pixels or carrying another patient's coordinates.
    """
    if not isinstance(study, dict) or not isinstance(memory, dict):
        return {
            "outcome": "invalid_input",
            "reason": "study_and_memory_must_be_objects",
            "objects": {},
        }
    cases = memory.get("cases", ())
    known = (
        sorted(
            {
                subject
                for case in cases
                if isinstance(case, Mapping)
                for subject in (
                    (case.get("subject"),)
                    if isinstance(case.get("subject"), str)
                    and not case["subject"].startswith("diagnosis/")
                    else ()
                )
            }
        )
        if isinstance(cases, Sequence) and not isinstance(cases, (str, bytes))
        else []
    )
    declared_objects = memory.get("objects", ())
    if isinstance(declared_objects, Sequence) and not isinstance(
        declared_objects, (str, bytes)
    ):
        known.extend(
            subject
            for subject in declared_objects
            if isinstance(subject, str)
            and not subject.startswith("diagnosis/")
            and subject not in known
        )
    objects: dict[str, Any] = {
        subject: {
            "status": "unresolved_missing_reading",
            "profile": None,
            "regions": [],
            "evidence": {"reason": "no_current_study_candidate_profiles"},
        }
        for subject in known
    }
    series, series_uids = _profile_candidates(study)
    if not series:
        return {
            "outcome": "unresolved_missing_reading",
            "study_uid": study.get("study_uid"),
            "objects": objects,
            "evidence": {"series_uids": series_uids, "searches_completed": 0},
        }
    # Derive object dimensions from each case's own declared window sizes, but
    # search those sizes at current-study coordinates only. No prior patient's
    # coordinates are copied into a candidate.
    priorities = memory.get("object_order", ())
    ordered = list(known)
    anchor_names = {"femur", "tibia", "patella", "fibula"}
    declared_anchors = memory.get("anchor_objects", ())
    if isinstance(declared_anchors, Sequence) and not isinstance(
        declared_anchors, (str, bytes)
    ):
        anchor_names.update(name for name in declared_anchors if isinstance(name, str))
    priority_sequence = (
        priorities
        if isinstance(priorities, Sequence) and not isinstance(priorities, (str, bytes))
        else ()
    )
    ordered = _object_order(ordered, priority_sequence, anchor_names)
    try:
        from knee.diagnosis.squint_profiles import profile_window
    except ImportError:
        profile_window = None
    from knee.diagnosis.squint_geometry import (
        object_geometry,
        relative_scope_priors,
        window_scope_codes,
    )

    case_records = (
        list(cases)
        if isinstance(cases, Sequence) and not isinstance(cases, (str, bytes))
        else []
    )
    series_by_uid = {
        record.get("series_uid"): record
        for record in series
        if isinstance(record.get("series_uid"), str)
    }
    coarse_indexes = {
        id(series_record): _coarse_index(series_record) for series_record in series
    }
    searches = 0
    geometry_by_subject: dict[str, dict[str, Any]] = {}
    for subject in ordered:
        if deadline is not None and time.monotonic() >= deadline:
            objects[subject]["evidence"] = {
                "reason": "deadline_before_search",
                "deadline_reached": True,
            }
            continue
        subject_cases = (
            [
                case
                for case in cases
                if isinstance(case, Mapping)
                and case.get("subject") == subject
                and _banks(case.get("profile")) is not None
            ]
            if isinstance(cases, Sequence)
            else []
        )
        base_banks = [_banks(case.get("profile")) for case in subject_cases]
        default_scope = {
            "cases": subject_cases,
            "banks": base_banks,
            "procedures": [
                _source(case.get("profile")).get("procedure") for case in subject_cases
            ],
            "matrix": _case_matrix(base_banks),
            "examples": _profile_exemplars(cases, subject)
            if isinstance(cases, Sequence)
            else [],
            "source": "view_unspecified_compatibility",
        }
        scope_cache: dict[tuple[str, str, str] | None, dict[str, Any]] = {}
        scope_evidence: dict[str, dict[str, Any]] = {}
        subject_anchors = _anchor_names(subject, set(known))
        relative_priors = relative_scope_priors(
            subject, subject_anchors, case_records, geometry_by_subject
        )
        prior_scope_codes: dict[str, int] = {}

        def scope_for(
            view: tuple[str, str, str] | None,
            _scope_cache: dict[
                tuple[str, str, str] | None, dict[str, Any]
            ] = scope_cache,
            _subject: str = subject,
            _cases: Sequence[Any] = cases,
        ) -> dict[str, Any]:
            if view not in _scope_cache:
                scoped_cases, scoped_examples, source = _location_scope(
                    _cases if isinstance(_cases, Sequence) else (), _subject, view
                )
                banks = [_banks(case.get("profile")) for case in scoped_cases]
                _scope_cache[view] = {
                    "cases": scoped_cases,
                    "banks": banks,
                    "procedures": [
                        _source(case.get("profile")).get("procedure")
                        for case in scoped_cases
                    ],
                    "matrix": _case_matrix(banks),
                    "examples": scoped_examples,
                    "source": source,
                }
            return _scope_cache[view]

        by_view: dict[tuple[str, str, str] | None, dict[str, Any]] = {}
        exact_case_best: dict[str, dict[str, Any]] = {}

        def consider(
            candidate: dict[str, Any],
            series_record: Mapping[str, Any],
            scope: Mapping[str, Any] = default_scope,
            _by_view: dict[tuple[str, str, str] | None, dict[str, Any]] = by_view,
            _exact_case_best: dict[str, dict[str, Any]] = exact_case_best,
        ) -> None:
            _precedents = scope["cases"]
            _precedent_banks = scope["banks"]
            _precedent_procedures = scope["procedures"]
            _precedent_matrix = scope["matrix"]
            query_banks = _banks(candidate.get("profile"))
            if query_banks is None:
                return
            query_procedure = _source(candidate.get("profile")).get("procedure")
            procedure_compatibility = [
                query_procedure == procedure for procedure in _precedent_procedures
            ]
            evidences = _batch_terms(
                query_banks,
                _precedent_banks,
                matrix_cache=_precedent_matrix,
                compatible=procedure_compatibility,
            )
            best: tuple[int, int] | None = None
            case_scores: list[tuple[Mapping[str, Any], tuple[int, int]]] = []
            for case, evidence in zip(_precedents, evidences, strict=True):
                if evidence is None or evidence.get("code") != "ok":
                    continue
                ratio = evidence["cosine_squared"]
                case_scores.append((case, ratio))
                if best is None or ratio[0] * best[1] > best[0] * ratio[1]:
                    best = ratio
            if best is None:
                return
            nonlocal searches
            searches += 1
            for case, ratio in case_scores:
                case_id = case.get("case_id")
                if not isinstance(case_id, str):
                    continue
                current = _exact_case_best.get(case_id)
                row = {
                    "profile": candidate["profile"],
                    "series_uid": series_record.get("series_uid"),
                    "view": series_record.get("view"),
                    "window": candidate.get("window"),
                    "centre_lps": candidate.get("centre_lps"),
                }
                if current is None or ratio[0] * current["score"][1] > (
                    current["score"][0] * ratio[1]
                ):
                    _exact_case_best[case_id] = {"score": ratio, "items": [row]}
                elif ratio[0] * current["score"][1] == (current["score"][0] * ratio[1]):
                    current["items"].append(row)
            key = _view_key(series_record.get("view"))
            group = _by_view.get(key)
            row = (candidate, series_record)
            if (
                group is None
                or best[0] * group["score"][1] > group["score"][0] * best[1]
            ):
                _by_view[key] = {"score": best, "items": [row], "count": 1}
            elif best[0] * group["score"][1] == group["score"][0] * best[1]:
                group["items"].append(row)
                group["count"] += 1
            else:
                group["count"] += 1

        for series_record in series:
            current_view = _view_key(series_record.get("view"))
            location_scope = scope_for(current_view)
            scope_key = json.dumps(current_view, separators=(",", ":"))
            scope_evidence[scope_key] = {
                "view": None if current_view is None else list(current_view),
                "source": location_scope["source"],
                "case_ids": [
                    case.get("case_id")
                    for case in location_scope["cases"]
                    if isinstance(case.get("case_id"), str)
                ],
            }
            if not location_scope["cases"]:
                continue
            stack = series_record.get("stack")
            median = getattr(stack, "median", None)
            if median is None or getattr(stack, "code", None) != "present":
                windows = series_record.get("candidate_profiles", ())
                if isinstance(windows, Sequence) and not isinstance(
                    windows, (str, bytes)
                ):
                    for item in windows:
                        if (
                            isinstance(item, Mapping)
                            and item.get("subject") == subject
                            and _banks(item.get("profile")) is not None
                        ):
                            consider(dict(item), series_record, location_scope)
                continue
            z_count, row_count, col_count = median.shape
            sizes: set[tuple[int, int, int]] = set()
            for exemplar, region in location_scope["examples"]:
                source_view = _view_key(_source(exemplar).get("view"))
                region_view = _view_key(region.get("view"))
                wanted_view = region_view or source_view
                if (
                    wanted_view is not None
                    and current_view is not None
                    and wanted_view != current_view
                ):
                    continue
                size = _window_size(region, exemplar)
                if size is not None:
                    sizes.add(
                        (
                            min(size[0], z_count),
                            min(size[1], row_count),
                            min(size[2], col_count),
                        )
                    )
            if location_scope["examples"] and not sizes:
                continue
            if not sizes:
                sizes.add((1, 1, 1))
            if profile_window is None:
                # Tests and lightweight callers may provide writer-cached
                # candidates; production installs the shared profile writer.
                windows = series_record.get("candidate_profiles", ())
                if isinstance(windows, Sequence) and not isinstance(
                    windows, (str, bytes)
                ):
                    for item in windows:
                        if (
                            isinstance(item, Mapping)
                            and item.get("subject") == subject
                            and _banks(item.get("profile")) is not None
                        ):
                            consider(dict(item), series_record, location_scope)
                continue
            lower, upper, foreground = _leg_bounds(stack)
            z_lo, r_lo, c_lo = lower
            z_hi, r_hi, c_hi = upper
            coarse_names, integrals = coarse_indexes[id(series_record)]
            if not coarse_names:
                continue
            case_vectors, case_bank_masks = _case_coarse_matrix(
                location_scope["cases"], coarse_names, location_scope["banks"]
            )
            best_by_case: dict[int, dict[str, Any]] = {}
            pending_windows: list[tuple[int, ...]] = []

            def flush_windows(
                _pending_windows: list[tuple[int, ...]] = pending_windows,
                _coarse_names: Sequence[str] = coarse_names,
                _integrals: Mapping[str, np.ndarray] = integrals,
                _case_vectors: np.ndarray = case_vectors,
                _case_bank_masks: np.ndarray = case_bank_masks,
                _best_by_case: dict[int, dict[str, Any]] = best_by_case,
                _series_record: dict[str, Any] = series_record,
                _relative_priors: dict[str, Any] = relative_priors,
                _prior_scope_codes: dict[str, int] = prior_scope_codes,
            ) -> None:
                if not _pending_windows:
                    return
                scope_codes = window_scope_codes(
                    _series_record, _pending_windows, _relative_priors
                )
                eligible_windows = []
                for window, scope_code in zip(
                    _pending_windows, scope_codes, strict=True
                ):
                    _prior_scope_codes[scope_code] = (
                        _prior_scope_codes.get(scope_code, 0) + 1
                    )
                    if scope_code != "outside_anatomical_prior":
                        eligible_windows.append(window)
                _pending_windows.clear()
                if not eligible_windows:
                    return
                vectors, vector_banks = _window_coarse_batch(
                    _coarse_names, _integrals, eligible_windows
                )
                scores_by_window = _coarse_case_scores_batch(
                    vectors, vector_banks, _case_vectors, _case_bank_masks
                )
                for window, scores in zip(
                    eligible_windows, scores_by_window, strict=True
                ):
                    for case_ordinal, score in enumerate(scores):
                        if score is None:
                            continue
                        current = _best_by_case.get(case_ordinal)
                        if current is None or score[0] * current["score"][1] > (
                            current["score"][0] * score[1]
                        ):
                            _best_by_case[case_ordinal] = {
                                "score": score,
                                "windows": [window],
                            }
                        elif score[0] * current["score"][1] == (
                            current["score"][0] * score[1]
                        ):
                            current["windows"].append(window)
                _pending_windows.clear()

            for ez, er, ec in sorted(sizes):
                for z0 in _window_starts(z_count, ez):
                    if z0 < z_lo or z0 + ez > z_hi:
                        continue
                    for r0 in _window_starts(row_count, er):
                        if r0 < r_lo or r0 + er > r_hi:
                            continue
                        for c0 in _window_starts(col_count, ec):
                            if c0 < c_lo or c0 + ec > c_hi:
                                continue
                            if deadline is not None and time.monotonic() >= deadline:
                                break
                            window = (z0, z0 + ez, r0, r0 + er, c0, c0 + ec)
                            if not bool(
                                foreground[
                                    z0 : z0 + ez, r0 : r0 + er, c0 : c0 + ec
                                ].any()
                            ):
                                continue
                            pending_windows.append(window)
                            if len(pending_windows) >= 128:
                                flush_windows()
                        if deadline is not None and time.monotonic() >= deadline:
                            break
                    if deadline is not None and time.monotonic() >= deadline:
                        break
                if deadline is not None and time.monotonic() >= deadline:
                    break
            flush_windows()
            finalists = {
                window
                for result in best_by_case.values()
                for window in result["windows"]
            }
            for window in sorted(finalists):
                if deadline is not None and time.monotonic() >= deadline:
                    break
                profile = profile_window(dict(series_record), window, subject=subject)
                if _banks(profile) is None:
                    continue
                consider(
                    {
                        "subject": subject,
                        "window": window,
                        "profile": profile,
                    },
                    series_record,
                    location_scope,
                )
        if not by_view:
            objects[subject]["evidence"] = {
                "reason": "no_compatible_current_study_candidates",
                "series_uids": series_uids,
            }
            continue
        constraints = memory.get("anatomical_constraints", ())
        relevant_constraints = (
            [
                row
                for row in constraints
                if isinstance(row, Mapping) and row.get("child") == subject
            ]
            if isinstance(constraints, Sequence)
            and not isinstance(constraints, (str, bytes))
            else []
        )
        chosen: list[tuple[dict[str, Any], Mapping[str, Any], tuple[int, int]]] = []
        candidate_profiles: list[dict[str, Any]] = []
        geometry_regions: list[dict[str, Any]] = []
        for group in by_view.values():
            kept: list[tuple[dict[str, Any], Mapping[str, Any]]] = []
            for candidate, series_record in group["items"]:
                excluded = False
                for constraint in relevant_constraints:
                    parent = constraint.get("parent")
                    parent_geometry = (
                        geometry_by_subject.get(parent)
                        if isinstance(parent, str)
                        else None
                    )
                    parent_reference = (
                        parent_geometry.get("reference")
                        if isinstance(parent_geometry, Mapping)
                        else None
                    )
                    parent_point = (
                        parent_reference.get("point_lps")
                        if isinstance(parent_reference, Mapping)
                        and parent_reference.get("status") == "complete"
                        else None
                    )
                    if parent_point is None or candidate.get("centre_lps") is None:
                        continue
                    point = candidate["centre_lps"]
                    distance = (
                        sum((point[i] - parent_point[i]) ** 2 for i in range(3)) ** 0.5
                    )
                    low, high = (
                        constraint.get("min_distance_mm", 0),
                        constraint.get("max_distance_mm"),
                    )
                    if isinstance(low, (int, float)) and distance < low:
                        excluded = True
                    if isinstance(high, (int, float)) and distance > high:
                        excluded = True
                if excluded:
                    continue
                kept.append((candidate, series_record))
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
                geometry_regions.append(
                    {
                        "series_uid": series_record.get("series_uid"),
                        "view": series_record.get("view"),
                        "window": candidate.get("window")
                        or _source(candidate.get("profile")).get("window"),
                    }
                )
            if len(kept) == 1:
                candidate, series_record = kept[0]
                chosen.append((candidate, series_record, group["score"]))
        if not candidate_profiles:
            objects[subject]["evidence"] = {
                "reason": "anatomical_constraints_removed_candidates",
                "candidate_view_count": len(by_view),
            }
            continue
        spatial_constraints = object_geometry(subject, geometry_regions, series_by_uid)
        geometry_by_subject[subject] = spatial_constraints
        profiles = [candidate["profile"] for candidate, _record, _score in chosen]
        merged_profile = None
        if profiles:
            try:
                from knee.diagnosis.squint_profiles import merge_profiles

                merged_profile = merge_profiles(profiles, subject=subject)
            except (ImportError, ValueError):
                if len(profiles) == 1:
                    merged_profile = profiles[0]
        case_best_candidates = [
            {
                "case_id": case_id,
                "squared_similarity": {
                    "numerator": str(result["score"][0]),
                    "denominator": str(result["score"][1]),
                },
                "candidates": result["items"],
            }
            for case_id, result in sorted(exact_case_best.items())
        ]
        candidate_catalogs = _intern_candidate_profiles(
            candidate_profiles, case_best_candidates
        )
        objects[subject] = {
            "status": "proposal",
            "profile": merged_profile,
            "candidate_profiles": candidate_profiles,
            "regions": geometry_regions,
            "evidence": {
                "source": "current_study_squint_grid_candidate",
                "candidate_view_count": len(by_view),
                "selected_view_regions": len(chosen),
                "candidate_profiles_compared": searches,
                "supporting_case_count": len(subject_cases),
                "location_scope_codes": dict(sorted(prior_scope_codes.items())),
                "location_precedent_scopes": [
                    scope_evidence[key] for key in sorted(scope_evidence)
                ],
                "spatial_constraints": spatial_constraints,
                "relative_scope_priors": relative_priors,
                "case_best_candidates": case_best_candidates,
                "candidate_profile_catalog": candidate_catalogs["profiles"],
                "candidate_bank_catalog": candidate_catalogs["banks"],
                "candidate_series_context_catalog": candidate_catalogs[
                    "series_contexts"
                ],
                "patient_coordinates_carried": False,
                "leg_background_prior": "coverage_and_scan_lowest_maximum",
            },
        }
    return {
        "outcome": "located_with_proposals",
        "study_uid": study.get("study_uid"),
        "objects": objects,
        "evidence": {
            "series_uids": series_uids,
            "candidate_profiles_compared": searches,
        },
    }


def recall_object(
    profile: dict, memory: dict, question: str, exclude_study_uid: str = ""
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
    query_banks = _banks(profile)
    if subject is None or query_banks is None:
        return {
            "outcome": "invalid_input",
            "reason": "invalid_profile",
            "question_id": question_id,
            "case_terms": [],
            "censor_terms": [],
            "speaking_calls": [],
        }
    prepared = memory.get("prepared_recall")
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
    if not isinstance(question_envelopes, Mapping):
        question_envelopes = {}
    if not question_envelopes:
        base["envelope_status"] = "unavailable_proposal_only"
    records: list[tuple[int, tuple[int, int], dict[str, Any]]] = []
    case_profile_banks = prepared.get("case_profile_banks", {})
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
            continue
        banks = case_profile_banks.get(case_index)
        if banks is None:
            banks = _banks(case.get("profile"))
        selected_cases.append((case_index, case, sign, banks))
    aligned_banks = [banks for _case_index, _case, _sign, banks in selected_cases]
    query_procedure = _source(profile).get("procedure")
    procedure_compatibility = [
        query_procedure == _source(case.get("profile")).get("procedure")
        for _case_index, case, _sign, _banks_value in selected_cases
    ]
    subject_matrices = prepared.get("subject_profile_matrices", {})
    matrix_cache = (
        subject_matrices.get(subject) if isinstance(subject_matrices, Mapping) else None
    )
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
            continue
        if evidence.get("code") == "silent":
            if isinstance(case_id, str):
                base["silent_case_ids"].append(case_id)
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
            "terms": {
                key: evidence[key] for key in ("dot", "left_norm_sq", "right_norm_sq")
            },
            "common_speaking_banks": evidence["common_speaking_banks"],
            "squared_cosine": {
                "numerator": str(ratio[0]),
                "denominator": str(ratio[1]),
            },
            "reaches_empirical_envelope": reaches,
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
            evidence = _terms(profile, censor.get("profile"))
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
