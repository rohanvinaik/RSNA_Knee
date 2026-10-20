"""Intent tests for exact named profile differences and preserved silence."""

from __future__ import annotations

import json

from knee.diagnosis.explanation import compare_named_profiles
from knee.diagnosis.models import Profile, Question
from knee.encoding.counts import BankLayout, CountBundle, CountLayout
from knee.encoding.places import (
    BankSpec,
    CompiledLayout,
    LayoutSpec,
    MetricKind,
    MetricSpec,
    compile_layout,
)

_REFERENCE = "a" * 64


def _layout(
    *, facet: str = "anatomy", state_words: tuple[str, ...] = ("round", "linear")
) -> CompiledLayout:
    compiled = compile_layout(
        LayoutSpec(
            "named-test-v1",
            "test-carrier",
            (
                BankSpec(
                    "shape",
                    facet,
                    (
                        MetricSpec("signal", MetricKind.DIGIT),
                        MetricSpec("state", MetricKind.WORDS, state_words),
                    ),
                ),
                BankSpec(
                    "context",
                    "setting",
                    (MetricSpec("view_code", MetricKind.WORDS, ("near", "far")),),
                ),
            ),
        )
    )
    assert compiled is not None
    return compiled


def _bundle(
    layout: CompiledLayout,
    reference: str = _REFERENCE,
    counts: dict[tuple[str, str, str], int] | None = None,
) -> CountBundle:
    rows = {bank.name: [0] * 512 for bank in layout.banks}
    for (bank_name, metric_name, row_name), count in (counts or {}).items():
        metric_rows = next(
            row
            for row in layout.metric_rows
            if row.bank == bank_name and row.metric == metric_name
        )
        rows[bank_name][metric_rows.start + metric_rows.names.index(row_name)] = count
    bound = CountLayout(
        f"{layout.version}:{layout.fingerprint}:{reference}",
        layout.carrier_id,
        tuple(BankLayout(bank.name, 512) for bank in layout.banks),
    )
    return CountBundle(bound, tuple(tuple(bank_rows) for bank_rows in rows.values()))


def _profile(
    bundle: CountBundle,
    *,
    subject: str = "acl",
    mode: str = "full",
    scope: str = "object:acl",
    context: tuple[tuple[str, str], ...] = (),
) -> Profile:
    return Profile(subject, bundle, mode, scope, "study-source", context=context)


def _question(
    *, banks: tuple[str, ...] = ("shape", "context"), context_keys: tuple[str, ...] = ()
) -> Question:
    return Question(
        "acl-state", "acl", ("acl",), banks=banks, context_keys=context_keys
    )


def test_common_rows_have_exact_names_counts_signed_delta_and_cosine_terms() -> None:
    layout = _layout()
    left = _profile(
        _bundle(
            layout,
            counts={
                ("shape", "signal", "+1"): 4,
                ("shape", "state", "round"): 2,
                ("context", "view_code", "near"): 3,
            },
        )
    )
    right = _profile(
        _bundle(
            layout,
            counts={
                ("shape", "signal", "+1"): 1,
                ("shape", "state", "round"): 1,
                ("context", "view_code", "near"): 1,
            },
        )
    )

    result = compare_named_profiles(
        left, layout, _REFERENCE, right, layout, _REFERENCE, _question()
    )
    json.dumps(result, allow_nan=False)

    assert result["code"] == "ok"
    assert result["selected_banks"] == ["shape", "context"]
    assert result["cosine_terms"] == {
        "dot": 9,
        "left_norm_sq": 29,
        "right_norm_sq": 3,
        "common_speaking_banks": ["shape", "context"],
    }
    banks = result["banks"]
    assert isinstance(banks, list)
    shape = banks[0]
    assert shape["facet"] == "anatomy"
    assert shape["status"] == "common"
    metrics = shape["metrics"]
    signal = metrics[0]
    plus_one = next(row for row in signal["rows"] if row["row"] == "+1")
    minus_one = next(row for row in signal["rows"] if row["row"] == "-1")
    assert plus_one == {
        "row": "+1",
        "left_count": 4,
        "right_count": 1,
        "count_delta": 3,
    }
    assert minus_one == {
        "row": "-1",
        "left_count": 0,
        "right_count": 0,
        "count_delta": 0,
    }


def test_signed_delta_preserves_direction_without_diagnosis_meaning() -> None:
    layout = _layout()
    left = _profile(_bundle(layout, counts={("shape", "signal", "-1"): 1}))
    right = _profile(_bundle(layout, counts={("shape", "signal", "-1"): 5}))

    result = compare_named_profiles(
        left, layout, _REFERENCE, right, layout, _REFERENCE, _question()
    )

    rows = result["banks"][0]["metrics"][0]["rows"]
    negative_row = next(row for row in rows if row["row"] == "-1")
    assert negative_row["count_delta"] == -4
    assert "diagnosis" not in result
    assert "label" not in result


def test_one_sided_and_silent_metrics_keep_missing_side_null() -> None:
    layout = _layout()
    left = _profile(_bundle(layout, counts={("shape", "signal", "0"): 2}))
    right = _profile(_bundle(layout))

    result = compare_named_profiles(
        left, layout, _REFERENCE, right, layout, _REFERENCE, _question()
    )

    assert result["code"] == "silent"
    assert result["cosine_terms"] is None
    shape = result["banks"][0]
    assert shape["status"] == "left_only"
    assert shape["cosine_included"] is False
    signal = shape["metrics"][0]
    assert signal["status"] == "left_only"
    middle = next(row for row in signal["rows"] if row["row"] == "0")
    assert middle == {
        "row": "0",
        "left_count": 2,
        "right_count": None,
        "count_delta": None,
    }
    silent_state = shape["metrics"][1]
    assert silent_state["status"] == "silent"
    assert all(
        row["left_count"] is None and row["right_count"] is None
        for row in silent_state["rows"]
    )


def test_layout_and_reference_mismatches_are_named_before_comparison() -> None:
    layout = _layout()
    other_layout = _layout(facet="different-anatomy")
    left = _profile(_bundle(layout))
    same_layout_right = _profile(_bundle(layout, reference="b" * 64))

    reference_result = compare_named_profiles(
        left,
        layout,
        _REFERENCE,
        same_layout_right,
        layout,
        "b" * 64,
        _question(),
    )
    layout_result = compare_named_profiles(
        left,
        layout,
        _REFERENCE,
        _profile(_bundle(other_layout)),
        other_layout,
        _REFERENCE,
        _question(),
    )

    assert reference_result == {
        "schema": "knee.diagnostic-named-comparison/v1",
        "code": "reference_set_mismatch",
    }
    assert layout_result["code"] == "layout_declaration_mismatch"


def test_wrong_bundle_reference_and_undeclared_rows_are_refused() -> None:
    layout = _layout()
    left = _profile(_bundle(layout))
    wrong_bound_bundle = _profile(_bundle(layout, reference="b" * 64))
    wrong_bound = compare_named_profiles(
        left, layout, _REFERENCE, wrong_bound_bundle, layout, _REFERENCE, _question()
    )

    counts = [list(bank) for bank in _bundle(layout).counts]
    counts[0][511] = 1
    malformed_bundle = CountBundle(
        _bundle(layout).layout, tuple(tuple(bank) for bank in counts)
    )
    malformed = compare_named_profiles(
        left,
        layout,
        _REFERENCE,
        _profile(malformed_bundle),
        layout,
        _REFERENCE,
        _question(),
    )

    assert wrong_bound["code"] == "bundle_layout_identity_mismatch"
    assert malformed["code"] == "invalid_named_count_bundle"


def test_context_incompatibility_and_missing_question_banks_are_named() -> None:
    layout = _layout()
    left = _profile(_bundle(layout), context=(("view", "Sag"),))
    right = _profile(_bundle(layout), context=(("view", "Cor"),))
    question = _question(context_keys=("view",))

    context_result = compare_named_profiles(
        left, layout, _REFERENCE, right, layout, _REFERENCE, question
    )
    bank_result = compare_named_profiles(
        left,
        layout,
        _REFERENCE,
        right,
        layout,
        _REFERENCE,
        _question(banks=("absent",)),
    )

    assert context_result["code"] == "profile_context_or_encoding_mismatch"
    assert bank_result["code"] == "question_banks_missing_from_layout"


def test_invalid_profiles_layouts_and_reference_identifiers_have_named_codes() -> None:
    layout = _layout()
    profile = _profile(_bundle(layout))
    invalid_layout = compare_named_profiles(
        profile, layout, _REFERENCE, profile, object(), _REFERENCE, _question()
    )
    invalid_reference = compare_named_profiles(
        profile, layout, "not-a-reference", profile, layout, _REFERENCE, _question()
    )
    invalid_profile = compare_named_profiles(
        object(), layout, _REFERENCE, profile, layout, _REFERENCE, _question()
    )

    assert invalid_layout["code"] == "invalid_compiled_layout"
    assert invalid_reference["code"] == "invalid_reference_identity"
    assert invalid_profile["code"] == "invalid_profile"


def test_malformed_question_and_nonbundle_profile_are_named_refusals() -> None:
    layout = _layout()
    valid_bundle = _bundle(layout)
    valid_profile = _profile(valid_bundle)
    malformed_question = Question(
        "acl-state", "acl", ("acl",), banks=("shape", "shape")
    )
    nonbundle_profile = Profile("acl", object(), "full", "object:acl", "study-source")

    invalid_question = compare_named_profiles(
        valid_profile,
        layout,
        _REFERENCE,
        valid_profile,
        layout,
        _REFERENCE,
        malformed_question,
    )
    invalid_bundle = compare_named_profiles(
        nonbundle_profile,
        layout,
        _REFERENCE,
        valid_profile,
        layout,
        _REFERENCE,
        _question(),
    )

    assert invalid_question["code"] == "invalid_question"
    assert invalid_bundle["code"] == "invalid_bundle"


def test_question_subject_mode_and_scope_mismatches_are_named() -> None:
    layout = _layout()
    profile = _profile(_bundle(layout))
    wrong_subject_question = Question("bone", "femur", ("femur",), banks=("shape",))
    different_mode = _profile(_bundle(layout), mode="cheap")
    different_scope = _profile(_bundle(layout), scope="region:acl")

    subject_result = compare_named_profiles(
        profile,
        layout,
        _REFERENCE,
        profile,
        layout,
        _REFERENCE,
        wrong_subject_question,
    )
    mode_result = compare_named_profiles(
        profile, layout, _REFERENCE, different_mode, layout, _REFERENCE, _question()
    )
    scope_result = compare_named_profiles(
        profile, layout, _REFERENCE, different_scope, layout, _REFERENCE, _question()
    )

    assert subject_result["code"] == "question_subject_mismatch"
    assert mode_result["code"] == "profile_mode_or_scope_mismatch"
    assert scope_result["code"] == "profile_mode_or_scope_mismatch"


def test_left_bundle_identity_mismatch_is_named() -> None:
    layout = _layout()
    left = _profile(_bundle(layout, reference="b" * 64))
    right = _profile(_bundle(layout))

    result = compare_named_profiles(
        left, layout, _REFERENCE, right, layout, _REFERENCE, _question()
    )

    assert result["code"] == "bundle_layout_identity_mismatch"


def test_profile_with_duplicate_context_keys_is_refused() -> None:
    layout = _layout()
    malformed = _profile(_bundle(layout), context=(("view", "Sag"), ("view", "Cor")))
    valid = _profile(_bundle(layout))

    result = compare_named_profiles(
        malformed, layout, _REFERENCE, valid, layout, _REFERENCE, _question()
    )

    assert result["code"] == "invalid_profile"
