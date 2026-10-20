"""Uncalibrated numeric readout of symbolic recall evidence.

Categorical present/absent calls remain exact 1/0. Unresolved calls receive a
relative, uncalibrated HDC resemblance grade from compatible signed case terms;
that grade is not a clinical posterior or a new diagnostic decision.
"""

from __future__ import annotations

import math
from collections.abc import Mapping
from fractions import Fraction
from typing import Any

from knee.diagnosis.declarations import QUESTIONS

__all__ = [
    "LABELS",
    "POLICY_ID",
    "ReadoutError",
    "probabilities_for_study",
    "readout_study",
]

LABELS = tuple(question.question_id for question in QUESTIONS)
POLICY_ID = "knee.diagnostic-readout/hdc-max-signed-squared-cosine-v1"

_CATEGORICAL = {"present": 1.0, "absent": 0.0}
_UNCERTAIN = frozenset(
    {
        "unresolved_conflict",
        "unresolved_censored",
        "proposal",
        "unresolved_missing_reading",
        "incompatible_encoding",
        "unresolved_no_precedent",
    }
)
_ALLOWED_OUTCOMES = frozenset((*_CATEGORICAL, *_UNCERTAIN, "invalid_input"))
_SIGNS = frozenset((-1, 1))


class ReadoutError(ValueError):
    """A named malformed readout evidence error."""

    def __init__(self, code: str, detail: str = "") -> None:
        super().__init__(f"{code}:{detail}" if detail else code)
        self.code = code
        self.detail = detail


def _plain_nonnegative_int(value: object) -> bool:
    return type(value) is int and value >= 0


def _plain_positive_int(value: object) -> bool:
    return type(value) is int and value > 0


def _record_ids(
    record: Mapping[str, Any], field: str, condition: str
) -> frozenset[str]:
    values = record.get(field, [])
    if (
        not isinstance(values, list)
        or any(not isinstance(item, str) or not item for item in values)
        or len(set(values)) != len(values)
    ):
        raise ReadoutError(f"{field}_invalid", condition)
    return frozenset(values)


def _case_terms(record: Mapping[str, Any], condition: str) -> list[dict[str, Any]]:
    terms = record.get("case_terms", [])
    if not isinstance(terms, list):
        raise ReadoutError("case_terms_not_list", condition)
    seen_ids: set[str] = set()
    checked: list[dict[str, Any]] = []
    ineligible_ids = frozenset().union(
        *(
            _record_ids(record, field, condition)
            for field in (
                "excluded_case_ids",
                "incompatible_case_ids",
                "silent_case_ids",
            )
        )
    )
    for index, item in enumerate(terms):
        where = f"{condition}:{index}"
        if not isinstance(item, Mapping):
            raise ReadoutError("case_term_not_object", where)
        case_id = item.get("case_id")
        if not isinstance(case_id, str) or not case_id:
            raise ReadoutError("case_id_invalid", where)
        if case_id in seen_ids:
            raise ReadoutError("duplicate_case_id", f"{condition}:{case_id}")
        if case_id in ineligible_ids:
            raise ReadoutError("ineligible_case_has_terms", f"{condition}:{case_id}")
        seen_ids.add(case_id)
        call = item.get("call")
        if type(call) is not int or call not in _SIGNS:
            raise ReadoutError("case_call_invalid", f"{condition}:{case_id}")
        raw = item.get("terms")
        if not isinstance(raw, Mapping):
            raise ReadoutError("cosine_terms_missing", f"{condition}:{case_id}")
        dot = raw.get("dot")
        left_norm = raw.get("left_norm_sq")
        right_norm = raw.get("right_norm_sq")
        if not _plain_nonnegative_int(dot):
            raise ReadoutError("cosine_dot_invalid", f"{condition}:{case_id}")
        if not _plain_positive_int(left_norm) or not _plain_positive_int(right_norm):
            raise ReadoutError("cosine_norm_invalid", f"{condition}:{case_id}")
        product = left_norm * right_norm
        if dot * dot > product:
            raise ReadoutError("cosine_terms_impossible", f"{condition}:{case_id}")
        banks = item.get("common_speaking_banks")
        if (
            not isinstance(banks, list)
            or not banks
            or any(not isinstance(bank, str) or not bank for bank in banks)
            or len(set(banks)) != len(banks)
        ):
            raise ReadoutError(
                "common_speaking_banks_invalid", f"{condition}:{case_id}"
            )
        checked.append(
            {
                "case_id": case_id,
                "call": call,
                "similarity": Fraction(dot * dot, product),
            }
        )
    return checked


def _vetoes(record: Mapping[str, Any], condition: str) -> frozenset[int]:
    values = record.get("vetoed_answers", [])
    if not isinstance(values, list):
        raise ReadoutError("vetoed_answers_not_list", condition)
    if any(type(value) is not int or value not in _SIGNS for value in values):
        raise ReadoutError("vetoed_answer_invalid", condition)
    if len(set(values)) != len(values):
        raise ReadoutError("duplicate_vetoed_answer", condition)
    return frozenset(values)


def _best_support(
    terms: list[dict[str, Any]], sign: int, vetoes: frozenset[int]
) -> tuple[Fraction, bool, list[str]]:
    if sign in vetoes:
        return Fraction(0, 1), False, []
    matching = [item for item in terms if item["call"] == sign]
    if not matching:
        return Fraction(0, 1), False, []
    best = max(item["similarity"] for item in matching)
    tied = [item["case_id"] for item in matching if item["similarity"] == best]
    return best, True, tied


def _fraction_record(value: Fraction) -> dict[str, str]:
    return {"numerator": str(value.numerator), "denominator": str(value.denominator)}


def _record_context(
    record: Mapping[str, Any], condition: str
) -> tuple[str | None, list[str]]:
    reason = record.get("reason")
    if reason is not None and not isinstance(reason, str):
        raise ReadoutError("recall_reason_invalid", condition)
    censor_ids = record.get("censor_ids", [])
    if (
        not isinstance(censor_ids, list)
        or any(not isinstance(item, str) or not item for item in censor_ids)
        or len(set(censor_ids)) != len(censor_ids)
    ):
        raise ReadoutError("censor_ids_invalid", condition)
    return reason, list(censor_ids)


def _endpoint_safe_float(value: Fraction) -> float:
    result = float(value)
    if result <= 0.0:
        return math.nextafter(0.0, 1.0)
    if result >= 1.0:
        return math.nextafter(1.0, 0.0)
    return result


def _read_condition(condition: str, raw: object) -> tuple[float, dict[str, Any]]:
    if not isinstance(raw, Mapping):
        raise ReadoutError("condition_record_not_object", condition)
    outcome = raw.get("outcome")
    if not isinstance(outcome, str) or outcome not in _ALLOWED_OUTCOMES:
        raise ReadoutError("outcome_invalid", condition)
    if outcome == "invalid_input":
        raise ReadoutError("invalid_recall_evidence", condition)
    terms = _case_terms(raw, condition)
    vetoes = _vetoes(raw, condition)
    recall_reason, censor_ids = _record_context(raw, condition)
    if outcome in _CATEGORICAL:
        probability = _CATEGORICAL[outcome]
        return probability, {
            "policy_id": POLICY_ID,
            "outcome": outcome,
            "kind": "symbolic",
            "reason": f"symbolic_{outcome}",
            "recall_reason": recall_reason,
            "positive_support": None,
            "negative_support": None,
            "grade_exact": None,
            "positive_case_ids": [],
            "negative_case_ids": [],
            "vetoed_answers": sorted(vetoes),
            "censor_ids": censor_ids,
        }

    positive, positive_available, positive_ids = _best_support(terms, 1, vetoes)
    negative, negative_available, negative_ids = _best_support(terms, -1, vetoes)
    exact = (Fraction(1, 1) + positive - negative) / 2
    if not positive_available and not negative_available:
        reason = "no_eligible_signed_support_neutral"
    elif positive_available and not negative_available:
        reason = "positive_support_only"
    elif negative_available and not positive_available:
        reason = "negative_support_only"
    else:
        reason = "both_signs_compared"
    return _endpoint_safe_float(exact), {
        "policy_id": POLICY_ID,
        "outcome": outcome,
        "kind": "graded_uncertainty",
        "reason": reason,
        "positive_support": {
            **_fraction_record(positive),
            "available": positive_available,
        },
        "negative_support": {
            **_fraction_record(negative),
            "available": negative_available,
        },
        "grade_exact": _fraction_record(exact),
        "positive_case_ids": positive_ids,
        "negative_case_ids": negative_ids,
        "vetoed_answers": sorted(vetoes),
        "censor_ids": censor_ids,
        "recall_reason": recall_reason,
    }


def readout_study(
    records: Mapping[str, Any],
) -> tuple[dict[str, float], dict[str, dict[str, Any]]]:
    """Read one study's twelve question records into probabilities and detail.

    The input is the mapping supplied to the pipeline's per-study readout
    callback. Categorical recall calls map exactly to 1/0; all declared
    uncertainty outcomes use only exact signed `case_terms` and `vetoed_answers`.
    """
    if not isinstance(records, Mapping):
        raise ReadoutError("study_records_not_object")
    keys = set(records)
    expected = set(LABELS)
    if keys != expected:
        missing = tuple(label for label in LABELS if label not in keys)
        extra = tuple(sorted((key for key in keys - expected), key=repr))
        if missing:
            raise ReadoutError("condition_records_missing", ",".join(missing))
        raise ReadoutError("condition_records_unknown", ",".join(map(str, extra)))
    probabilities: dict[str, float] = {}
    details: dict[str, dict[str, Any]] = {}
    for label in LABELS:
        probability, detail = _read_condition(label, records[label])
        probabilities[label] = probability
        details[label] = detail
    return probabilities, details


def probabilities_for_study(records: Mapping[str, Any]) -> dict[str, float]:
    """Return only the flat twelve-condition probability mapping."""
    probabilities, _ = readout_study(records)
    return probabilities
