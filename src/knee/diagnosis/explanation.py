"""Named, exact count differences for compatible retained HDC profiles."""

from __future__ import annotations

from collections.abc import Sequence

from knee.diagnosis.models import Profile, Question
from knee.diagnosis.retrieval import (
    _compatible,
    _selected_banks,
    _valid_profile,
    _valid_question,
)
from knee.encoding.counts import (
    BankLayout,
    CountBundle,
    CountCode,
    CountLayout,
    cosine_terms,
)
from knee.encoding.places import (
    CompiledLayout,
    LayoutSpec,
    compile_layout,
    decode_count_names,
)

_SCHEMA = "knee.diagnostic-named-comparison/v1"


def _invalid(code: str) -> dict[str, object]:
    return {"schema": _SCHEMA, "code": code}


def _reference_id_valid(value: object) -> bool:
    return (
        isinstance(value, str)
        and len(value) == 64
        and all(character in "0123456789abcdef" for character in value)
    )


def _verified_layout(layout: object) -> CompiledLayout | None:
    if not isinstance(layout, CompiledLayout):
        return None
    rebuilt = compile_layout(
        LayoutSpec(layout.version, layout.carrier_id, layout.banks)
    )
    if rebuilt != layout:
        return None
    return layout


def _expected_count_layout(
    layout: CompiledLayout, reference_set_fingerprint: str
) -> CountLayout:
    return CountLayout(
        layout_id=(
            f"{layout.version}:{layout.fingerprint}:{reference_set_fingerprint}"
        ),
        carrier_id=layout.carrier_id,
        banks=tuple(
            BankLayout(bank.name, count_bank.row_count)
            for bank, count_bank in zip(
                layout.banks, layout.count_layout.banks, strict=True
            )
        ),
    )


def _profile_identity(profile: Profile) -> dict[str, str]:
    return {"subject": profile.subject, "mode": profile.mode, "scope": profile.scope}


def _named_counts(
    layout: CompiledLayout, bundle: CountBundle, reference_id: str
) -> tuple[tuple[str, str, str, str, int], ...] | None:
    return decode_count_names(layout, bundle, reference_id)


def _metric_status(left: Sequence[int], right: Sequence[int]) -> str:
    left_speaks = any(left)
    right_speaks = any(right)
    if left_speaks and right_speaks:
        return "common"
    if left_speaks:
        return "left_only"
    if right_speaks:
        return "right_only"
    return "silent"


def _bank_status(metric_statuses: Sequence[str]) -> str:
    left_speaks = any(status in ("common", "left_only") for status in metric_statuses)
    right_speaks = any(status in ("common", "right_only") for status in metric_statuses)
    if left_speaks and right_speaks:
        return "common"
    if left_speaks:
        return "left_only"
    if right_speaks:
        return "right_only"
    return "silent"


def compare_named_profiles(
    left: Profile,
    left_layout: CompiledLayout,
    left_reference_set_fingerprint: str,
    right: Profile,
    right_layout: CompiledLayout,
    right_reference_set_fingerprint: str,
    question: Question,
) -> dict[str, object]:
    """Compare compatible profiles and name their exact declared count rows.

    The left profile is the query and the right is the recalled case. A row
    delta is emitted only when both profiles speak for that metric. A missing
    metric remains one-sided/silent, never an implicit all-zero measurement.
    """
    if not isinstance(left, Profile) or not isinstance(right, Profile):
        return _invalid("invalid_profile")
    if not isinstance(question, Question) or not _valid_question(question):
        return _invalid("invalid_question")
    if not _valid_profile(left) or not _valid_profile(right):
        return _invalid("invalid_profile")
    if not isinstance(left.bundle, CountBundle) or not isinstance(
        right.bundle, CountBundle
    ):
        return _invalid("invalid_bundle")
    checked_left_layout = _verified_layout(left_layout)
    checked_right_layout = _verified_layout(right_layout)
    if checked_left_layout is None or checked_right_layout is None:
        return _invalid("invalid_compiled_layout")
    if not _reference_id_valid(
        left_reference_set_fingerprint
    ) or not _reference_id_valid(right_reference_set_fingerprint):
        return _invalid("invalid_reference_identity")

    if checked_left_layout != checked_right_layout:
        return _invalid("layout_declaration_mismatch")
    if left_reference_set_fingerprint != right_reference_set_fingerprint:
        return _invalid("reference_set_mismatch")

    if left.bundle.layout != _expected_count_layout(
        checked_left_layout, left_reference_set_fingerprint
    ) or right.bundle.layout != _expected_count_layout(
        checked_right_layout, right_reference_set_fingerprint
    ):
        return _invalid("bundle_layout_identity_mismatch")

    if left.subject != question.subject or right.subject != question.subject:
        return _invalid("question_subject_mismatch")
    if left.mode != right.mode or left.scope != right.scope:
        return _invalid("profile_mode_or_scope_mismatch")
    if not _compatible(left, right, question):
        return _invalid("profile_context_or_encoding_mismatch")

    selected_banks = _selected_banks(left, question)
    if not selected_banks:
        return _invalid("question_banks_missing_from_layout")

    left_names = _named_counts(
        checked_left_layout, left.bundle, left_reference_set_fingerprint
    )
    right_names = _named_counts(
        checked_right_layout, right.bundle, right_reference_set_fingerprint
    )
    if left_names is None or right_names is None:
        return _invalid("invalid_named_count_bundle")

    left_counts = {
        (bank, metric, row): count for bank, _facet, metric, row, count in left_names
    }
    right_counts = {
        (bank, metric, row): count for bank, _facet, metric, row, count in right_names
    }
    comparison = cosine_terms(left.bundle, right.bundle, selected_banks)
    if comparison.code is CountCode.INVALID_INPUT:
        return _invalid("invalid_comparison_input")
    if comparison.code is CountCode.IDENTITY_MISMATCH:
        return _invalid("comparison_identity_mismatch")

    bank_records: list[dict[str, object]] = []
    common_bank_names = set(
        () if comparison.terms is None else comparison.terms.included_banks
    )
    for bank_name in selected_banks:
        bank_spec = next(
            (bank for bank in checked_left_layout.banks if bank.name == bank_name),
            None,
        )
        if bank_spec is None:
            return _invalid("question_bank_not_declared")
        metric_records: list[dict[str, object]] = []
        metric_states: list[str] = []
        for metric in bank_spec.metrics:
            row_names = next(
                item.names
                for item in checked_left_layout.metric_rows
                if item.bank == bank_name and item.metric == metric.name
            )
            left_row_counts = [
                left_counts[(bank_name, metric.name, row)] for row in row_names
            ]
            right_row_counts = [
                right_counts[(bank_name, metric.name, row)] for row in row_names
            ]
            status = _metric_status(left_row_counts, right_row_counts)
            metric_states.append(status)
            rows: list[dict[str, object]] = []
            for row_name, left_count, right_count in zip(
                row_names, left_row_counts, right_row_counts, strict=True
            ):
                both_speak = status == "common"
                rows.append(
                    {
                        "row": row_name,
                        "left_count": left_count
                        if status in ("common", "left_only")
                        else None,
                        "right_count": right_count
                        if status in ("common", "right_only")
                        else None,
                        "count_delta": (
                            left_count - right_count if both_speak else None
                        ),
                    }
                )
            metric_records.append(
                {"metric": metric.name, "status": status, "rows": rows}
            )
        bank_records.append(
            {
                "bank": bank_name,
                "facet": bank_spec.facet,
                "status": _bank_status(metric_states),
                "cosine_included": bank_name in common_bank_names,
                "metrics": metric_records,
            }
        )

    terms: dict[str, object] | None
    if comparison.code is CountCode.SILENT:
        terms = None
    elif comparison.terms is None:
        return _invalid("comparison_terms_missing")
    else:
        terms = {
            "dot": comparison.terms.dot,
            "left_norm_sq": comparison.terms.left_norm_sq,
            "right_norm_sq": comparison.terms.right_norm_sq,
            "common_speaking_banks": list(comparison.terms.included_banks),
        }
    return {
        "schema": _SCHEMA,
        "code": "silent" if comparison.code is CountCode.SILENT else "ok",
        "left": _profile_identity(left),
        "right": _profile_identity(right),
        "selected_banks": list(selected_banks),
        "count_delta_convention": "left_count - right_count",
        "cosine_terms": terms,
        "banks": bank_records,
    }
