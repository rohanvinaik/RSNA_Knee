"""Individual-case exact retrieval for contextual diagnostic memory."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from knee.diagnosis.models import Case, Censor, Profile, Question, Snapshot, Trust
from knee.encoding import counts as _counts
from knee.encoding.counts import (
    CountCode,
    compare_cosine_pairs,
    cosine_reaches_level,
    cosine_terms,
)

_SIGNS = (-1, 1)


@dataclass(frozen=True, slots=True)
class PreparedSnapshot:
    """Snapshot-scoped validation facts; holds no derived global cache."""

    snapshot: Snapshot
    case_nonzero_banks: tuple[tuple[str, ...] | None, ...]
    censor_nonzero_banks: tuple[tuple[str, ...] | None, ...]
    error: dict[str, Any] | None = None


@dataclass(frozen=True, slots=True)
class PreparedQuestion:
    """Query-bound projection plan reusable for repeated recall calls."""

    query: Profile
    question: Question
    snapshot: PreparedSnapshot
    projected_query: Profile | None
    projected_question: Question | None
    selected_banks: tuple[str, ...]
    error: dict[str, Any] | None = None
    case_eligibility: tuple[str, ...] = ()
    censor_eligibility: tuple[str, ...] = ()


def _bundle_nonzero_banks(profile: Profile) -> tuple[str, ...] | None:
    if not _counts._valid_bundle(profile.bundle):
        return None
    return tuple(
        bank.name
        for bank, rows in zip(
            profile.bundle.layout.banks, profile.bundle.counts, strict=True
        )
        if any(rows)
    )


def prepare_snapshot(snapshot: Snapshot) -> PreparedSnapshot:
    """Validate immutable snapshot profiles once and retain bank activity facts.

    The returned value is local to the caller. It is safe to reuse for multiple
    queries while the frozen Snapshot remains unchanged.
    """
    if not isinstance(snapshot, Snapshot) or not isinstance(snapshot.revision, str):
        return PreparedSnapshot(snapshot, (), (), _invalid("invalid_snapshot"))
    if (
        not isinstance(snapshot.cases, tuple)
        or not isinstance(snapshot.trust, tuple)
        or not isinstance(snapshot.censors, tuple)
    ):
        return PreparedSnapshot(
            snapshot, (), (), _invalid("invalid_snapshot_collections")
        )
    if any(not isinstance(case, Case) for case in snapshot.cases):
        return PreparedSnapshot(snapshot, (), (), _invalid("invalid_case_record"))
    if len(
        {case.case_id for case in snapshot.cases if isinstance(case.case_id, str)}
    ) != len(snapshot.cases):
        return PreparedSnapshot(
            snapshot, (), (), _invalid("duplicate_or_invalid_case_id")
        )
    if any(
        not isinstance(trust, Trust) or not _valid_trust(trust)
        for trust in snapshot.trust
    ):
        return PreparedSnapshot(snapshot, (), (), _invalid("invalid_trust_record"))
    if any(
        not isinstance(censor, Censor) or not _valid_censor(censor)
        for censor in snapshot.censors
    ):
        return PreparedSnapshot(snapshot, (), (), _invalid("invalid_censor_record"))
    trust_keys = [(trust.case_id, trust.question) for trust in snapshot.trust]
    if len(set(trust_keys)) != len(trust_keys):
        return PreparedSnapshot(
            snapshot, (), (), _invalid("duplicate_case_question_trust")
        )
    censor_ids = [censor.censor_id for censor in snapshot.censors]
    if len(set(censor_ids)) != len(censor_ids):
        return PreparedSnapshot(snapshot, (), (), _invalid("duplicate_censor_id"))

    case_nonzero = tuple(
        _bundle_nonzero_banks(case.profile) if _valid_profile(case.profile) else None
        for case in snapshot.cases
    )
    censor_nonzero = tuple(
        _bundle_nonzero_banks(censor.profile)
        if _valid_profile(censor.profile)
        else None
        for censor in snapshot.censors
    )
    return PreparedSnapshot(snapshot, case_nonzero, censor_nonzero)


def _project_profile(profile: Profile, bank_names: tuple[str, ...]) -> Profile:
    layout = profile.bundle.layout
    indices = {bank.name: index for index, bank in enumerate(layout.banks)}
    projected_layout = type(layout)(
        layout.layout_id,
        layout.carrier_id,
        tuple(layout.banks[indices[name]] for name in bank_names),
    )
    projected_bundle = type(profile.bundle)(
        projected_layout,
        tuple(profile.bundle.counts[indices[name]] for name in bank_names),
    )
    return Profile(
        subject=profile.subject,
        bundle=projected_bundle,
        mode=profile.mode,
        scope=profile.scope,
        source_id=profile.source_id,
        context=profile.context,
        bank_statuses=profile.bank_statuses,
        provenance=profile.provenance,
    )


def prepare_question(
    query: Profile, question: Question, snapshot: PreparedSnapshot
) -> PreparedQuestion:
    """Project one query/question onto banks the original cosine can include.

    A query-silent selected bank is omitted because the public cosine helper
    would omit it for every candidate. All remaining counts and the original
    layout/carrier/reference identity are retained.
    """
    if snapshot.error is not None:
        return PreparedQuestion(
            query, question, snapshot, None, None, (), snapshot.error
        )
    if not _valid_profile(query) or not _valid_question(question):
        return PreparedQuestion(
            query,
            question,
            snapshot,
            None,
            None,
            (),
            _invalid("invalid_query_or_question"),
        )
    if query.subject != question.subject:
        return PreparedQuestion(
            query,
            question,
            snapshot,
            None,
            None,
            (),
            {
                "outcome": "incompatible_encoding",
                "reason": "query_subject_does_not_match_question",
                "question_id": question.question_id,
                "query_subject": query.subject,
                "question_subject": question.subject,
            },
        )
    selected = _selected_banks(query, question)
    if not selected:
        return PreparedQuestion(
            query,
            question,
            snapshot,
            None,
            None,
            (),
            {
                "outcome": "incompatible_encoding",
                "reason": "question_banks_not_present_in_query_layout",
                "question_id": question.question_id,
                "selected_banks": [],
            },
        )
    if not _counts._valid_bundle(query.bundle):
        return PreparedQuestion(
            query,
            question,
            snapshot,
            None,
            None,
            selected,
            _invalid("invalid_query_bundle_or_question_banks"),
        )
    query_nonzero = {
        bank.name
        for bank, rows in zip(
            query.bundle.layout.banks, query.bundle.counts, strict=True
        )
        if any(rows)
    }
    projected_names = tuple(name for name in selected if name in query_nonzero)
    if not projected_names:
        # Every selected bank is silent in the query, so the original cosine
        # excludes all of them. One declared bank preserves a valid silent
        # bundle; the public result retains the complete selection separately.
        projected_names = (selected[0],)
    projected_query = _project_profile(query, projected_names)
    projected_question = Question(
        question_id=question.question_id,
        subject=question.subject,
        objects=question.objects,
        banks=projected_names,
        context_keys=question.context_keys,
    )

    projected_cases: list[Case] = []
    case_eligibility: list[str] = []
    for case, nonzero in zip(
        snapshot.snapshot.cases, snapshot.case_nonzero_banks, strict=True
    ):
        profile = case.profile
        try:
            originally_compatible = _valid_profile(profile) and _compatible(
                query, profile, question
            )
        except (AttributeError, TypeError):
            return PreparedQuestion(
                query,
                question,
                snapshot,
                None,
                None,
                selected,
                _invalid("malformed_snapshot_or_question_data"),
            )
        if not originally_compatible:
            case_eligibility.append("incompatible")
            projected_cases.append(case)
        elif nonzero is None:
            case_eligibility.append("invalid_bundle")
            projected_cases.append(case)
        else:
            case_eligibility.append("eligible")
            projected_cases.append(
                Case(
                    case.case_id,
                    case.study_uid,
                    _project_profile(profile, projected_names),
                    case.calls,
                    case.teaching_revision,
                )
            )
    projected_censors: list[Censor] = []
    censor_eligibility: list[str] = []
    for censor, nonzero in zip(
        snapshot.snapshot.censors, snapshot.censor_nonzero_banks, strict=True
    ):
        profile = censor.profile
        if censor.question != question.question_id:
            censor_eligibility.append("not_selected")
            projected_censors.append(censor)
        else:
            try:
                originally_compatible = _valid_profile(profile) and _compatible(
                    query, profile, question
                )
            except (AttributeError, TypeError):
                return PreparedQuestion(
                    query,
                    question,
                    snapshot,
                    None,
                    None,
                    selected,
                    _invalid("malformed_snapshot_or_question_data"),
                )
            if not originally_compatible:
                censor_eligibility.append("incompatible")
                projected_censors.append(censor)
            elif nonzero is None:
                censor_eligibility.append("invalid_bundle")
                projected_censors.append(censor)
            else:
                censor_eligibility.append("eligible")
                projected_censors.append(
                    Censor(
                        censor.censor_id,
                        censor.question,
                        censor.answer,
                        _project_profile(profile, projected_names),
                        censor.numerator,
                        censor.denominator,
                        censor.source,
                    )
                )
    projected_snapshot = Snapshot(
        snapshot.snapshot.revision,
        tuple(projected_cases),
        snapshot.snapshot.trust,
        tuple(projected_censors),
        snapshot.snapshot.schema_version,
    )

    def project_activity(activity: tuple[str, ...] | None) -> tuple[str, ...] | None:
        if activity is None:
            return None
        active = set(activity)
        return tuple(name for name in projected_names if name in active)

    projected_prepared = PreparedSnapshot(
        projected_snapshot,
        tuple(project_activity(item) for item in snapshot.case_nonzero_banks),
        tuple(project_activity(item) for item in snapshot.censor_nonzero_banks),
    )
    return PreparedQuestion(
        query,
        question,
        projected_prepared,
        projected_query,
        projected_question,
        selected,
        case_eligibility=tuple(case_eligibility),
        censor_eligibility=tuple(censor_eligibility),
    )


def _plain_int(value: object) -> bool:
    return isinstance(value, int) and not isinstance(value, bool)


def _valid_profile(profile: object) -> bool:
    valid = (
        isinstance(profile, Profile)
        and isinstance(profile.subject, str)
        and bool(profile.subject)
        and isinstance(profile.mode, str)
        and bool(profile.mode)
        and isinstance(profile.scope, str)
        and bool(profile.scope)
        and isinstance(profile.source_id, str)
        and bool(profile.source_id)
        and isinstance(profile.context, tuple)
        and all(
            isinstance(pair, tuple)
            and len(pair) == 2
            and isinstance(pair[0], str)
            and isinstance(pair[1], str)
            for pair in profile.context
        )
    )
    return valid and len({key for key, _ in profile.context}) == len(profile.context)


def _valid_question(question: object) -> bool:
    if not isinstance(question, Question):
        return False
    if not all(
        isinstance(value, str) and value
        for value in (question.question_id, question.subject)
    ):
        return False
    if not isinstance(question.objects, tuple) or not all(
        isinstance(value, str) and value for value in question.objects
    ):
        return False
    if not isinstance(question.banks, tuple) or not all(
        isinstance(value, str) and value for value in question.banks
    ):
        return False
    if not isinstance(question.bank_prefixes, tuple) or not all(
        isinstance(value, str) and value for value in question.bank_prefixes
    ):
        return False
    if not isinstance(question.context_keys, tuple) or not all(
        isinstance(value, str) and value for value in question.context_keys
    ):
        return False
    if len(set(question.banks)) != len(question.banks):
        return False
    if len(set(question.bank_prefixes)) != len(question.bank_prefixes):
        return False
    if len(set(question.context_keys)) != len(question.context_keys):
        return False
    return bool(question.banks or question.bank_prefixes)


def _selected_banks(profile: Profile, question: Question) -> tuple[str, ...] | None:
    layout = profile.bundle.layout
    names = tuple(bank.name for bank in layout.banks)
    if question.banks:
        if any(name not in names for name in question.banks):
            return None
        return question.banks
    return tuple(
        name
        for name in names
        if any(name.startswith(prefix) for prefix in question.bank_prefixes)
    )


def _compatible(query: Profile, candidate: Profile, question: Question) -> bool:
    if candidate.subject != question.subject or query.subject != question.subject:
        return False
    if candidate.mode != query.mode or candidate.scope != query.scope:
        return False
    # CountLayout equality carries the layout, carrier, bank order and the
    # reference identity declared by the encoder.
    if candidate.bundle.layout != query.bundle.layout:
        return False
    query_context = dict(query.context)
    candidate_context = dict(candidate.context)
    if len(query_context) != len(query.context) or len(candidate_context) != len(
        candidate.context
    ):
        return False
    return all(
        key in query_context
        and key in candidate_context
        and query_context[key] == candidate_context[key]
        for key in question.context_keys
    )


def _valid_trust(trust: Trust) -> bool:
    return (
        isinstance(trust.case_id, str)
        and bool(trust.case_id)
        and isinstance(trust.question, str)
        and bool(trust.question)
        and _plain_int(trust.numerator)
        and _plain_int(trust.denominator)
        and trust.denominator > 0
        and 0 <= trust.numerator <= trust.denominator
        and isinstance(trust.source, str)
        and bool(trust.source)
    )


def _valid_censor(censor: Censor) -> bool:
    return (
        isinstance(censor.censor_id, str)
        and bool(censor.censor_id)
        and isinstance(censor.question, str)
        and bool(censor.question)
        and _plain_int(censor.answer)
        and censor.answer in _SIGNS
        and _valid_profile(censor.profile)
        and _plain_int(censor.numerator)
        and _plain_int(censor.denominator)
        and censor.denominator > 0
        and 0 <= censor.numerator <= censor.denominator
        and isinstance(censor.source, str)
        and bool(censor.source)
    )


def _invalid(reason: str) -> dict[str, Any]:
    return {"outcome": "invalid_input", "reason": reason}


def _nearest_case_ids(
    query: Profile,
    candidates: list[dict[str, Any]],
    banks: tuple[str, ...],
) -> list[str]:
    if not candidates:
        return []
    best = candidates[0]
    nearest = [best["case_id"]]
    for candidate in candidates[1:]:
        comparison = compare_cosine_pairs(
            query.bundle,
            candidate["profile"].bundle,
            best["profile"].bundle,
            banks,
        )
        if comparison.code is CountCode.FIRST_NEARER:
            best = candidate
            nearest = [candidate["case_id"]]
        elif comparison.code is CountCode.TIE:
            nearest.append(candidate["case_id"])
    return nearest


def _case_record(
    case: Case,
    digit: int,
    terms: Any,
    trust: Trust | None,
    reaches: bool | None,
) -> dict[str, Any]:
    return {
        "case_id": case.case_id,
        "study_uid": case.study_uid,
        "call": digit,
        "terms": {
            "dot": terms.dot,
            "left_norm_sq": terms.left_norm_sq,
            "right_norm_sq": terms.right_norm_sq,
        },
        "common_speaking_banks": list(terms.included_banks),
        "trust": None
        if trust is None
        else {
            "numerator": trust.numerator,
            "denominator": trust.denominator,
            "source": trust.source,
        },
        "reaches_trust": reaches,
    }


def _find_question_call(case: Case, question_id: str) -> tuple[int | None, bool]:
    matches = [call for call in case.calls if call.question == question_id]
    if len(matches) > 1:
        raise ValueError("duplicate_question_call")
    if not matches:
        return None, False
    digit = matches[0].digit
    if not _plain_int(digit) or digit not in (-1, 0, 1):
        raise ValueError("invalid_call_digit")
    if not isinstance(matches[0].source, str) or not matches[0].source:
        raise ValueError("invalid_call_source")
    return digit, digit == 0


def _declared_source_group(profile: Profile) -> tuple[str | None, str | None]:
    """Return one explicit profile group, rejecting conflicting declarations."""
    declarations: list[str] = []
    for field_name in ("context", "provenance"):
        pairs = getattr(profile, field_name, None)
        if not isinstance(pairs, tuple) or not all(
            isinstance(pair, tuple)
            and len(pair) == 2
            and isinstance(pair[0], str)
            and isinstance(pair[1], str)
            for pair in pairs
        ):
            return None, "invalid_source_group_metadata"
        for key, value in pairs:
            if key == "source_group" and value:
                declarations.append(value)
    distinct = set(declarations)
    if len(distinct) > 1:
        return None, "conflicting_source_group_metadata"
    return (next(iter(distinct)) if distinct else None), None


def _recall_projected(
    query: Profile,
    question: Question,
    snapshot: Snapshot,
    *,
    exclude_study_uid: str = "",
    exclude_source_group: str = "",
    case_eligibility: tuple[str, ...] | None = None,
    censor_eligibility: tuple[str, ...] | None = None,
) -> dict[str, Any]:
    """Compare a query to individual compatible cases and preserve concurrence.

    Trust is supplied per case and question in the snapshot. Cases without trust
    remain proposals; no radius is inferred here. Exact count helpers decide the
    comparison and trust-boundary results.
    """
    if not _valid_profile(query) or not _valid_question(question):
        return _invalid("invalid_query_or_question")
    if not isinstance(snapshot, Snapshot) or not isinstance(snapshot.revision, str):
        return _invalid("invalid_snapshot")
    if not isinstance(exclude_study_uid, str):
        return _invalid("invalid_study_exclusion")
    if not isinstance(exclude_source_group, str):
        return _invalid("invalid_source_group_exclusion")
    if exclude_source_group:
        _, group_error = _declared_source_group(query)
        if group_error is not None:
            return _invalid(group_error)
    if query.subject != question.subject:
        return {
            "outcome": "incompatible_encoding",
            "reason": "query_subject_does_not_match_question",
            "question_id": question.question_id,
            "query_subject": query.subject,
            "question_subject": question.subject,
        }
    if (
        not isinstance(snapshot.cases, tuple)
        or not isinstance(snapshot.trust, tuple)
        or not isinstance(snapshot.censors, tuple)
    ):
        return _invalid("invalid_snapshot_collections")
    if case_eligibility is not None and len(case_eligibility) != len(snapshot.cases):
        return _invalid("prepared_case_eligibility_mismatch")
    if censor_eligibility is not None and len(censor_eligibility) != len(
        snapshot.censors
    ):
        return _invalid("prepared_censor_eligibility_mismatch")
    if any(not isinstance(case, Case) for case in snapshot.cases):
        return _invalid("invalid_case_record")
    if len(
        {case.case_id for case in snapshot.cases if isinstance(case.case_id, str)}
    ) != len(snapshot.cases):
        return _invalid("duplicate_or_invalid_case_id")
    if any(
        not isinstance(trust, Trust) or not _valid_trust(trust)
        for trust in snapshot.trust
    ):
        return _invalid("invalid_trust_record")
    if any(
        not isinstance(censor, Censor) or not _valid_censor(censor)
        for censor in snapshot.censors
    ):
        return _invalid("invalid_censor_record")
    trust_map: dict[tuple[str, str], Trust] = {}
    for trust in snapshot.trust:
        key = trust.case_id, trust.question
        if key in trust_map:
            return _invalid("duplicate_case_question_trust")
        trust_map[key] = trust
    censor_ids = [censor.censor_id for censor in snapshot.censors]
    if len(set(censor_ids)) != len(censor_ids):
        return _invalid("duplicate_censor_id")

    banks = _selected_banks(query, question)
    if not banks:
        return {
            "outcome": "incompatible_encoding",
            "reason": "question_banks_not_present_in_query_layout",
            "question_id": question.question_id,
            "selected_banks": [],
        }
    self_check = cosine_terms(query.bundle, query.bundle, banks)
    if self_check.code is CountCode.INVALID_INPUT:
        return _invalid("invalid_query_bundle_or_question_banks")
    if self_check.code is CountCode.IDENTITY_MISMATCH:
        return {
            "outcome": "incompatible_encoding",
            "reason": "query_bundle_identity_mismatch",
            "question_id": question.question_id,
            "selected_banks": list(banks),
        }

    base: dict[str, Any] = {
        "question_id": question.question_id,
        "subject": question.subject,
        "selected_banks": list(banks),
        "case_terms": [],
        "censor_terms": [],
        "speaking_case_ids": [],
        "speaking_calls": [],
        "excluded_case_ids": [],
        "source_group_excluded_case_ids": [],
        "excluded_source_group": exclude_source_group,
        "incompatible_case_ids": [],
        "silent_case_ids": [],
        "nearest_positive_case_ids": [],
        "nearest_negative_case_ids": [],
        "nearest_positive_case_id": None,
        "nearest_negative_case_id": None,
        "censor_ids": [],
        "vetoed_answers": [],
    }
    comparable_by_sign: dict[int, list[dict[str, Any]]] = {-1: [], 1: []}
    compatible_signed_count = 0
    compatible_silent_count = 0
    incompatible_signed_count = 0
    proposal_case_count = 0
    speaking_signs: set[int] = set()

    try:
        for case_index, case in enumerate(snapshot.cases):
            if (
                not isinstance(case.case_id, str)
                or not case.case_id
                or not isinstance(case.study_uid, str)
                or not case.study_uid
            ):
                return _invalid("invalid_case_identity")
            if not isinstance(case.calls, tuple) or not all(
                hasattr(call, "question") and hasattr(call, "digit")
                for call in case.calls
            ):
                return _invalid("invalid_case_calls")
            digit, abstained = _find_question_call(case, question.question_id)
            if digit is None:
                continue
            declared_group: str | None = None
            if exclude_source_group:
                declared_group, group_error = _declared_source_group(case.profile)
                if group_error is not None:
                    return _invalid(group_error)
            if exclude_study_uid and case.study_uid == exclude_study_uid:
                base["excluded_case_ids"].append(case.case_id)
                continue
            if exclude_source_group and declared_group == exclude_source_group:
                base["excluded_case_ids"].append(case.case_id)
                base["source_group_excluded_case_ids"].append(case.case_id)
                continue
            if abstained:
                continue
            if digit not in _SIGNS:
                return _invalid("invalid_call_digit")
            if case_eligibility is not None:
                eligibility = case_eligibility[case_index]
                if eligibility == "incompatible":
                    incompatible_signed_count += 1
                    base["incompatible_case_ids"].append(case.case_id)
                    continue
                if eligibility == "invalid_bundle":
                    return _invalid("invalid_case_bundle_or_bank_selection")
                if eligibility != "eligible":
                    return _invalid("prepared_case_eligibility_invalid")
            compatible = _valid_profile(case.profile) and _compatible(
                query, case.profile, question
            )
            if not compatible:
                incompatible_signed_count += 1
                base["incompatible_case_ids"].append(case.case_id)
                continue
            terms_result = cosine_terms(query.bundle, case.profile.bundle, banks)
            if terms_result.code is CountCode.IDENTITY_MISMATCH:
                incompatible_signed_count += 1
                base["incompatible_case_ids"].append(case.case_id)
                continue
            if terms_result.code is CountCode.INVALID_INPUT:
                return _invalid("invalid_case_bundle_or_bank_selection")
            compatible_signed_count += 1
            if terms_result.code is CountCode.SILENT:
                compatible_silent_count += 1
                base["silent_case_ids"].append(case.case_id)
                continue
            assert terms_result.terms is not None
            trust = trust_map.get((case.case_id, question.question_id))
            reaches: bool | None = None
            if trust is not None:
                trust_result = cosine_reaches_level(
                    query.bundle,
                    case.profile.bundle,
                    banks,
                    numerator=trust.numerator,
                    denominator=trust.denominator,
                )
                if trust_result.code is CountCode.INVALID_INPUT:
                    return _invalid("invalid_trust_comparison")
                if trust_result.code is CountCode.IDENTITY_MISMATCH:
                    incompatible_signed_count += 1
                    base["incompatible_case_ids"].append(case.case_id)
                    continue
                reaches = trust_result.code is CountCode.REACHES
            record = _case_record(case, digit, terms_result.terms, trust, reaches)
            base["case_terms"].append(record)
            comparable_by_sign[digit].append(
                {"case_id": case.case_id, "profile": case.profile, "record": record}
            )
            if trust is None or not reaches:
                proposal_case_count += 1
            else:
                speaking_signs.add(digit)
                base["speaking_case_ids"].append(case.case_id)
                base["speaking_calls"].append(digit)

        for sign in _SIGNS:
            nearest_ids = _nearest_case_ids(query, comparable_by_sign[sign], banks)
            key = (
                "nearest_positive_case_ids"
                if sign == 1
                else "nearest_negative_case_ids"
            )
            singular_key = (
                "nearest_positive_case_id" if sign == 1 else "nearest_negative_case_id"
            )
            base[key] = nearest_ids
            if len(nearest_ids) == 1:
                base[singular_key] = nearest_ids[0]

        vetoed: set[int] = set()
        compatible_censor_count = 0
        silent_censor_count = 0
        incompatible_censor_count = 0
        for censor_index, censor in enumerate(snapshot.censors):
            if censor.question != question.question_id:
                continue
            if censor_eligibility is not None:
                eligibility = censor_eligibility[censor_index]
                if eligibility == "not_selected":
                    return _invalid("prepared_censor_question_mismatch")
                if eligibility == "incompatible":
                    incompatible_censor_count += 1
                    continue
                if eligibility == "invalid_bundle":
                    return _invalid("invalid_censor_bundle_or_bank_selection")
                if eligibility != "eligible":
                    return _invalid("prepared_censor_eligibility_invalid")
            elif not _compatible(query, censor.profile, question):
                incompatible_censor_count += 1
                continue
            compatible_censor_count += 1
            terms_result = cosine_terms(query.bundle, censor.profile.bundle, banks)
            if terms_result.code is CountCode.IDENTITY_MISMATCH:
                incompatible_censor_count += 1
                continue
            if terms_result.code is CountCode.INVALID_INPUT:
                return _invalid("invalid_censor_bundle_or_bank_selection")
            if terms_result.code is CountCode.SILENT:
                silent_censor_count += 1
                continue
            assert terms_result.terms is not None
            threshold = cosine_reaches_level(
                query.bundle,
                censor.profile.bundle,
                banks,
                numerator=censor.numerator,
                denominator=censor.denominator,
            )
            if threshold.code is CountCode.INVALID_INPUT:
                return _invalid("invalid_censor_comparison")
            if threshold.code is CountCode.IDENTITY_MISMATCH:
                incompatible_censor_count += 1
                continue
            reaches = threshold.code is CountCode.REACHES
            base["censor_terms"].append(
                {
                    "censor_id": censor.censor_id,
                    "answer": censor.answer,
                    "source": censor.source,
                    "terms": {
                        "dot": terms_result.terms.dot,
                        "left_norm_sq": terms_result.terms.left_norm_sq,
                        "right_norm_sq": terms_result.terms.right_norm_sq,
                    },
                    "common_speaking_banks": list(terms_result.terms.included_banks),
                    "numerator": censor.numerator,
                    "denominator": censor.denominator,
                    "reaches_trust": reaches,
                }
            )
            if reaches:
                vetoed.add(censor.answer)
                base["censor_ids"].append(censor.censor_id)

        base["vetoed_answers"] = sorted(vetoed)
        if speaking_signs:
            remaining = speaking_signs - vetoed
            if remaining == {1, -1}:
                outcome = "unresolved_conflict"
            elif remaining == {1}:
                outcome = "present"
            elif remaining == {-1}:
                outcome = "absent"
            else:
                outcome = "unresolved_censored"
        elif vetoed:
            outcome = "unresolved_censored"
        elif proposal_case_count:
            outcome = "proposal"
        elif compatible_silent_count:
            outcome = "unresolved_missing_reading"
        elif base["case_terms"]:
            outcome = "proposal"
        elif compatible_signed_count:
            outcome = "unresolved_missing_reading"
        elif incompatible_signed_count or incompatible_censor_count:
            outcome = "incompatible_encoding"
        elif not snapshot.cases or not base["excluded_case_ids"]:
            outcome = "unresolved_no_precedent"
        else:
            outcome = "unresolved_no_precedent"

        base["outcome"] = outcome
        base["coverage"] = {
            "compatible_signed_cases": compatible_signed_count,
            "compatible_silent_cases": compatible_silent_count,
            "incompatible_signed_cases": incompatible_signed_count,
            "compatible_censors": compatible_censor_count,
            "silent_censors": silent_censor_count,
            "incompatible_censors": incompatible_censor_count,
        }
        return base
    except ValueError as exc:
        return _invalid(str(exc) or "malformed_snapshot_or_question_data")
    except (AttributeError, TypeError):
        return _invalid("malformed_snapshot_or_question_data")


def recall(
    query: Profile,
    question: Question,
    snapshot: Snapshot | PreparedSnapshot | PreparedQuestion,
    *,
    exclude_study_uid: str = "",
    exclude_source_group: str = "",
) -> dict[str, Any]:
    """Recall with optional reusable snapshot/question preparation.

    Passing a value from :func:`prepare_snapshot` avoids revalidating the
    original case matrices. Passing a value from :func:`prepare_question`
    additionally reuses its selected-bank projection and case evidence terms.
    """
    if not _valid_profile(query) or not _valid_question(question):
        return _invalid("invalid_query_or_question")
    if not isinstance(exclude_study_uid, str):
        return _invalid("invalid_study_exclusion")
    if not isinstance(exclude_source_group, str):
        return _invalid("invalid_source_group_exclusion")
    if exclude_source_group:
        _, group_error = _declared_source_group(query)
        if group_error is not None:
            return _invalid(group_error)
    if query.subject != question.subject:
        return {
            "outcome": "incompatible_encoding",
            "reason": "query_subject_does_not_match_question",
            "question_id": question.question_id,
            "query_subject": query.subject,
            "question_subject": question.subject,
        }
    if isinstance(snapshot, PreparedQuestion):
        plan = snapshot
        if query is not plan.query or question != plan.question:
            return _invalid("prepared_question_mismatch")
    else:
        prepared = (
            snapshot
            if isinstance(snapshot, PreparedSnapshot)
            else prepare_snapshot(snapshot)
        )
        plan = prepare_question(query, question, prepared)
    if plan.error is not None:
        return plan.error
    if plan.projected_query is None or plan.projected_question is None:
        return _invalid("prepared_question_incomplete")
    result = _recall_projected(
        plan.projected_query,
        plan.projected_question,
        plan.snapshot.snapshot,
        exclude_study_uid=exclude_study_uid,
        exclude_source_group=exclude_source_group,
        case_eligibility=plan.case_eligibility,
        censor_eligibility=plan.censor_eligibility,
    )
    if "selected_banks" in result:
        result["selected_banks"] = list(plan.selected_banks)
    return result
