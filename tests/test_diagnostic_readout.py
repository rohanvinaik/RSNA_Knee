"""Intent tests for the symbolic functional-competition readout.

Rohan's words behind these tests: the score is an area under the probability
curve; where the symbolic pipeline has graduated from principled abstention the
report is a clean 1 (present) or 0 (absent); where there is too much
uncertainty it reports a graded number from HDC cosine math.

Everything here builds evidence records by hand in the public ``recall`` row
convention (``case_terms`` rows with ``case_id``, ``call``,
``terms = {dot, left_norm_sq, right_norm_sq}``, and a nonempty
``common_speaking_banks`` list) and checks meaning, not the spelling of most
detail fields. ``policy_id``, ``outcome`` and ``reason`` are checked directly;
exact fractions and case identifiers are also inspected within a label's
details.
"""

from __future__ import annotations

import copy
import math
from fractions import Fraction

import pytest

from knee.diagnosis import readout
from knee.diagnosis.readout import (
    POLICY_ID,
    ReadoutError,
    probabilities_for_study,
    readout_study,
)
from knee.study.tables import LABELS

LABEL = LABELS[0]
OTHER_LABEL = LABELS[1]

GRADED_OUTCOMES = ("proposal", "unresolved_conflict", "unresolved_censored")
NO_EVIDENCE_OUTCOMES = ("unresolved_no_precedent", "unresolved_missing_reading")


# ---------------------------------------------------------------------------
# builders
# ---------------------------------------------------------------------------


def _term(
    case_id: str, call: int, dot: int, left: int, right: int | None = None
) -> dict:
    return {
        "case_id": case_id,
        "call": call,
        "terms": {
            "dot": dot,
            "left_norm_sq": left,
            "right_norm_sq": left if right is None else right,
        },
        "common_speaking_banks": ["shared"],
    }


def _ratio(case_id: str, call: int, k: int, m: int) -> dict:
    """A comparable row whose squared cosine is exactly (k/m)**2."""
    return _term(case_id, call, k, m, m)


def _sq(k: int, m: int) -> Fraction:
    return Fraction(k * k, m * m)


def _record(
    outcome: str,
    terms: tuple | list = (),
    *,
    vetoed: tuple | list = (),
    reason: str | None = None,
) -> dict:
    row: dict = {
        "outcome": outcome,
        "case_terms": [copy.deepcopy(item) for item in terms],
        "vetoed_answers": list(vetoed),
    }
    if reason is not None:
        row["reason"] = reason
    return row


def _study(**by_label: dict) -> dict:
    """Twelve records: every official label is 'absent' unless overridden."""
    records = {label: _record("absent") for label in LABELS}
    for name, row in by_label.items():
        records[name] = row
    return records


def _one(record: dict) -> tuple[float, object]:
    """Probability and details of the first official label for one record."""
    probabilities, details = readout_study(_study(**{LABEL: record}))
    return probabilities[LABEL], details[LABEL]


def _grade(positive: Fraction, negative: Fraction) -> Fraction:
    return (1 + positive - negative) / 2


def _interior(value: Fraction) -> float:
    rounded = float(value)
    if rounded >= 1.0:
        return math.nextafter(1.0, 0.0)
    if rounded <= 0.0:
        return math.nextafter(0.0, 1.0)
    return rounded


# ---------------------------------------------------------------------------
# helpers that look for meaning anywhere inside a details structure
# ---------------------------------------------------------------------------


def _is_int(value: object) -> bool:
    return isinstance(value, int) and not isinstance(value, bool)


def _numbers(value: object):
    if isinstance(value, Fraction):
        yield value
    elif isinstance(value, bool):
        return
    elif isinstance(value, int):
        yield Fraction(value)
    elif isinstance(value, float):
        if math.isfinite(value):
            yield Fraction(value)
    elif isinstance(value, str):
        try:
            yield Fraction(value)
        except (ValueError, ZeroDivisionError):
            pass
    elif isinstance(value, dict):
        if "numerator" in value and "denominator" in value:
            try:
                yield Fraction(int(value["numerator"]), int(value["denominator"]))
            except (TypeError, ValueError, ZeroDivisionError):
                pass
        for item in value.values():
            yield from _numbers(item)
    elif isinstance(value, (list, tuple)):
        if (
            len(value) == 2
            and _is_int(value[0])
            and _is_int(value[1])
            and value[1] != 0
        ):
            yield Fraction(value[0], value[1])
        for item in value:
            yield from _numbers(item)


def _carries_fraction(details: object, target: Fraction) -> bool:
    return any(number == target for number in _numbers(details))


def _strings(value: object):
    if isinstance(value, str):
        yield value
    elif isinstance(value, dict):
        for key, item in value.items():
            yield from _strings(key)
            yield from _strings(item)
    elif isinstance(value, (list, tuple, set, frozenset)):
        for item in value:
            yield from _strings(item)


def _values_for_key(value: object, key: str):
    if isinstance(value, dict):
        for name, item in value.items():
            if name == key:
                yield item
            yield from _values_for_key(item, key)
    elif isinstance(value, (list, tuple)):
        for item in value:
            yield from _values_for_key(item, key)


def _mentions(details: object, text: str) -> bool:
    return text in repr(details)


# ---------------------------------------------------------------------------
# named policy and error
# ---------------------------------------------------------------------------


def test_policy_id_and_error_code_are_named() -> None:
    assert isinstance(POLICY_ID, str)
    assert POLICY_ID.strip()
    assert issubclass(ReadoutError, Exception)
    with pytest.raises(ReadoutError) as caught:
        readout_study({})
    assert isinstance(caught.value.code, str)
    assert caught.value.code.strip()


def test_every_label_gets_a_probability_and_details_naming_the_policy() -> None:
    probabilities, details = readout_study(_study())

    assert set(probabilities) == set(LABELS)
    assert set(details) == set(LABELS)
    for label in LABELS:
        assert POLICY_ID in list(_values_for_key(details[label], "policy_id"))
        assert "absent" in list(_values_for_key(details[label], "outcome"))


def test_probabilities_for_study_is_the_probability_half_of_readout_study() -> None:
    records = _study(
        **{
            LABEL: _record("present"),
            OTHER_LABEL: _record(
                "proposal",
                [_ratio("a", 1, 1, 2), _ratio("b", -1, 1, 3)],
            ),
        }
    )
    probabilities, _ = readout_study(records)
    assert probabilities_for_study(records) == probabilities
    assert readout_study(records)[0] == probabilities  # deterministic


def test_readout_does_not_mutate_its_input_and_is_label_local() -> None:
    records = _study(
        **{OTHER_LABEL: _record("proposal", [_ratio("a", 1, 1, 2)], vetoed=[-1])}
    )
    before = copy.deepcopy(records)
    first = readout_study(records)
    assert records == before

    changed = copy.deepcopy(records)
    changed[LABEL] = _record("present")
    second = readout_study(changed)
    for label in LABELS:
        if label != LABEL:
            assert second[0][label] == first[0][label]
            assert second[1][label] == first[1][label]
    assert second[0][LABEL] == 1.0


# ---------------------------------------------------------------------------
# symbolic endpoints: a clean 1 and a clean 0, never inferred from similarity
# ---------------------------------------------------------------------------


def test_present_is_a_clean_one_and_absent_a_clean_zero() -> None:
    probabilities, _ = readout_study(
        _study(**{LABEL: _record("present"), OTHER_LABEL: _record("absent")})
    )
    assert probabilities[LABEL] == 1.0
    assert probabilities[OTHER_LABEL] == 0.0
    assert isinstance(probabilities[LABEL], float)
    assert isinstance(probabilities[OTHER_LABEL], float)


@pytest.mark.parametrize(
    ("outcome", "terms", "expected"),
    [
        # the symbolic outcome wins even when cosine proximity says otherwise
        ("present", [_ratio("far-neg", -1, 1, 1)], 1.0),
        ("present", [_ratio("pos-zero", 1, 0, 5), _ratio("neg", -1, 1, 1)], 1.0),
        ("absent", [_ratio("near-pos", 1, 1, 1)], 0.0),
        ("absent", [_ratio("pos", 1, 1, 1), _ratio("neg-zero", -1, 0, 5)], 0.0),
        ("present", [], 1.0),
        ("absent", [], 0.0),
    ],
)
def test_endpoints_are_independent_of_graded_similarity(
    outcome: str, terms: list, expected: float
) -> None:
    probability, details = _one(_record(outcome, terms))
    assert probability == expected
    assert type(probability) is float
    assert outcome in list(_values_for_key(details, "outcome"))


@pytest.mark.parametrize("outcome", GRADED_OUTCOMES)
def test_unresolved_state_never_reaches_an_endpoint_however_close(
    outcome: str,
) -> None:
    perfect_positive, _ = _one(_record(outcome, [_ratio("p", 1, 1, 1)]))
    perfect_negative, _ = _one(_record(outcome, [_ratio("n", -1, 1, 1)]))
    both, _ = _one(_record(outcome, [_ratio("p", 1, 1, 1), _ratio("n", -1, 1, 1)]))

    assert 0.0 < perfect_negative < both < perfect_positive < 1.0
    assert perfect_positive == math.nextafter(1.0, 0.0)
    assert perfect_negative == math.nextafter(0.0, 1.0)
    assert both == 0.5


# ---------------------------------------------------------------------------
# graded numerical computation, exact until the final float
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("outcome", GRADED_OUTCOMES)
@pytest.mark.parametrize(
    ("positive", "negative"),
    [
        ([(1, 2)], []),
        ([], [(1, 2)]),
        ([(1, 2)], [(1, 3)]),
        ([(3, 4)], [(1, 4)]),
        ([(1, 1)], [(1, 1)]),
        ([(0, 5)], [(0, 5)]),
        ([(2, 3)], [(1, 5)]),
    ],
)
def test_grade_is_one_plus_positive_minus_negative_over_two(
    outcome: str, positive: list, negative: list
) -> None:
    terms = [_ratio(f"p{i}", 1, k, m) for i, (k, m) in enumerate(positive)] + [
        _ratio(f"n{i}", -1, k, m) for i, (k, m) in enumerate(negative)
    ]
    pos = max((_sq(k, m) for k, m in positive), default=Fraction(0))
    neg = max((_sq(k, m) for k, m in negative), default=Fraction(0))
    grade = _grade(pos, neg)

    probability, details = _one(_record(outcome, terms))

    assert probability == _interior(grade)
    assert 0.0 < probability < 1.0
    assert _carries_fraction(details, grade)
    if positive:
        assert _carries_fraction(details, pos)
    if negative:
        assert _carries_fraction(details, neg)
    assert outcome in list(_values_for_key(details, "outcome"))


def test_squared_cosine_uses_all_three_term_numbers_not_only_the_dot() -> None:
    # dot=2, |l|^2=8, |r|^2=2 -> 4/16 = 1/4, unlike dot**2/left or dot/right
    probability, details = _one(_record("proposal", [_term("p", 1, 2, 8, 2)]))
    assert probability == float(_grade(Fraction(1, 4), Fraction(0)))
    assert _carries_fraction(details, Fraction(1, 4))


def test_opposing_evidence_is_monotone_in_both_directions() -> None:
    previous = -1.0
    for k in range(8):  # positive support (k/8)**2 grows, negative held at 1/9
        probability, _ = _one(
            _record("proposal", [_ratio("p", 1, k, 8), _ratio("n", -1, 1, 3)])
        )
        assert probability > previous
        previous = probability

    previous = 2.0
    for k in range(8):  # negative support grows, positive held at 1/9
        probability, _ = _one(
            _record("proposal", [_ratio("p", 1, 1, 3), _ratio("n", -1, k, 8)])
        )
        assert probability < previous
        previous = probability


def test_swapping_the_signs_reflects_the_probability_about_one_half() -> None:
    for left, right in [((1, 2), (1, 4)), ((3, 4), (1, 2)), ((1, 8), (7, 8))]:
        forward, _ = _one(
            _record("proposal", [_ratio("p", 1, *left), _ratio("n", -1, *right)])
        )
        mirror, _ = _one(
            _record("proposal", [_ratio("p", 1, *right), _ratio("n", -1, *left)])
        )
        assert forward + mirror == 1.0


def test_unresolved_probabilities_are_always_floats_strictly_inside() -> None:
    for pos_k in (0, 1, 2, 3, 4):
        for neg_k in (0, 1, 2, 3, 4):
            terms = [_ratio("p", 1, pos_k, 4), _ratio("n", -1, neg_k, 4)]
            probability, _ = _one(_record("proposal", terms))
            assert type(probability) is float
            assert 0.0 < probability < 1.0


# ---------------------------------------------------------------------------
# no sum or vote over duplicates; ties keep every identifier
# ---------------------------------------------------------------------------


def test_support_is_the_maximum_per_sign_not_a_sum_or_mean() -> None:
    probability, details = _one(
        _record(
            "proposal",
            [
                _ratio("weak", 1, 1, 4),  # 1/16
                _ratio("best", 1, 1, 2),  # 1/4
                _ratio("middle", 1, 1, 3),  # 1/9
                _ratio("opposed", -1, 1, 3),  # 1/9
            ],
        )
    )
    assert probability == float(_grade(Fraction(1, 4), Fraction(1, 9)))
    assert _carries_fraction(details, Fraction(1, 4))
    assert _mentions(details, "best")


def test_tied_nearest_cases_keep_every_id_and_do_not_add_support() -> None:
    single, _ = _one(_record("proposal", [_ratio("only", 1, 1, 2)]))
    probability, details = _one(
        _record(
            "proposal",
            [
                _ratio("z-case", 1, 1, 2),
                # same squared cosine, different integers: a tie by value
                _term("a-case", 1, 2, 8, 2),
                _term("m-case", 1, 3, 12, 3),
                _ratio("weaker", 1, 1, 3),
            ],
        )
    )
    assert probability == single == 0.625  # 1/4 once; a sum would give 3/4 or more
    for tied in ("z-case", "a-case", "m-case"):
        assert _mentions(details, tied)


def test_distinct_cases_with_identical_profiles_do_not_accumulate_votes() -> None:
    once, _ = _one(_record("proposal", [_ratio("dup", 1, 1, 2)]))
    thrice, details = _one(
        _record(
            "proposal",
            [
                _ratio("dup-a", 1, 1, 2),
                _ratio("dup-b", 1, 1, 2),
                _ratio("dup-c", 1, 1, 2),
            ],
        )
    )
    assert thrice == once == 0.625
    assert _carries_fraction(details, Fraction(1, 4))


def test_row_order_and_record_order_do_not_change_the_answer() -> None:
    terms = [
        _ratio("a", 1, 1, 2),
        _ratio("b", 1, 1, 2),
        _ratio("c", -1, 1, 3),
        _ratio("d", -1, 1, 5),
    ]
    forward = _one(_record("proposal", terms))
    backward = _one(_record("proposal", list(reversed(terms))))
    assert forward[0] == backward[0]
    for case_id in "abc":
        assert _mentions(forward[1], case_id) and _mentions(backward[1], case_id)

    records = _study(
        **{LABEL: _record("proposal", terms), OTHER_LABEL: _record("present")}
    )
    reordered = dict(reversed(list(records.items())))
    assert readout_study(reordered)[0] == readout_study(records)[0]


# ---------------------------------------------------------------------------
# missing sign versus measured orthogonality
# ---------------------------------------------------------------------------


def test_missing_sign_gives_zero_support_but_is_not_a_measured_zero() -> None:
    positive = _ratio("positive-case", 1, 1, 2)
    only_positive, missing_details = _one(_record("proposal", [positive]))
    orthogonal, orthogonal_details = _one(
        _record("proposal", [positive, _term("orthogonal-negative", -1, 0, 4, 4)])
    )

    # same number: zero numerical support either way ...
    assert only_positive == orthogonal == 0.625
    # ... but different knowledge: one sign was never measured, the other was
    assert missing_details != orthogonal_details
    assert _mentions(orthogonal_details, "orthogonal-negative")
    assert not _mentions(missing_details, "orthogonal-negative")
    lowered = repr(missing_details).lower()
    assert any(
        word in lowered for word in ("unavailable", "missing", "none", "null", "no_")
    )
    assert _carries_fraction(orthogonal_details, Fraction(0))


def test_missing_positive_is_symmetric_and_also_kept_in_details() -> None:
    probability, details = _one(_record("proposal", [_ratio("only-neg", -1, 1, 2)]))
    assert probability == 0.375
    assert _mentions(details, "only-neg")
    assert _carries_fraction(details, Fraction(1, 4))


@pytest.mark.parametrize("outcome", GRADED_OUTCOMES + NO_EVIDENCE_OUTCOMES)
def test_both_signs_missing_is_a_named_neutral_half_never_normal(
    outcome: str,
) -> None:
    probability, details = _one(_record(outcome))
    assert probability == 0.5
    assert type(probability) is float
    assert "normal" not in repr(details).lower()
    assert outcome in list(_values_for_key(details, "outcome"))

    orthogonal, orthogonal_details = _one(
        _record(outcome, [_term("zero-p", 1, 0, 3, 3), _term("zero-n", -1, 0, 3, 3)])
    )
    assert orthogonal == 0.5  # measured orthogonality is also one half ...
    assert details != orthogonal_details  # ... but it is not the same knowledge


def test_neutral_state_differs_from_the_symbolic_endpoints() -> None:
    _, neutral = _one(_record("unresolved_no_precedent"))
    _, absent = _one(_record("absent"))
    _, present = _one(_record("present"))
    assert neutral != absent
    assert neutral != present


# ---------------------------------------------------------------------------
# veto provenance
# ---------------------------------------------------------------------------


def test_vetoed_positive_answer_is_excluded_but_its_provenance_is_kept() -> None:
    terms = [_ratio("vetoed-near-miss", 1, 1, 1), _ratio("negative", -1, 1, 2)]
    open_probability, open_details = _one(_record("proposal", terms))
    vetoed_record = _record("unresolved_censored", terms, vetoed=[1])
    original_terms = copy.deepcopy(vetoed_record["case_terms"])
    vetoed_probability, vetoed_details = _one(vetoed_record)

    assert open_probability == _interior(_grade(Fraction(1), Fraction(1, 4)))
    # the vetoed positive supplies no number: (1 + 0 - 1/4) / 2
    assert vetoed_probability == float(Fraction(3, 8))
    assert vetoed_details != open_details
    assert vetoed_details["vetoed_answers"] == [1]
    assert vetoed_record["case_terms"] == original_terms
    assert _carries_fraction(vetoed_details, Fraction(3, 8))
    assert "unresolved_censored" in list(_values_for_key(vetoed_details, "outcome"))


def test_vetoed_negative_answer_is_excluded_symmetrically() -> None:
    probability, details = _one(
        _record(
            "unresolved_censored",
            [_ratio("positive", 1, 1, 2), _ratio("vetoed-negative", -1, 1, 1)],
            vetoed=[-1],
        )
    )
    assert probability == 0.625  # (1 + 1/4 - 0) / 2
    assert details["vetoed_answers"] == [-1]


def test_veto_removes_the_best_case_so_the_next_best_cannot_substitute() -> None:
    # A vetoed sign is excluded as a sign: a lesser case of the same sign
    # does not speak in its place.
    probability, _ = _one(
        _record(
            "unresolved_censored",
            [_ratio("best", 1, 1, 1), _ratio("lesser", 1, 1, 2)],
            vetoed=[1],
        )
    )
    assert probability == 0.5


def test_both_signs_vetoed_is_the_neutral_half() -> None:
    probability, details = _one(
        _record(
            "unresolved_censored",
            [_ratio("p", 1, 1, 1), _ratio("n", -1, 1, 1)],
            vetoed=[1, -1],
        )
    )
    assert probability == 0.5
    assert "normal" not in repr(details).lower()


def test_veto_never_alters_symbolic_endpoints() -> None:
    assert _one(_record("present", [_ratio("p", 1, 1, 1)], vetoed=[1]))[0] == 1.0
    assert _one(_record("absent", [_ratio("n", -1, 1, 1)], vetoed=[-1]))[0] == 0.0


# ---------------------------------------------------------------------------
# preserved reason and exact fractions
# ---------------------------------------------------------------------------


def test_reason_outcome_policy_and_exact_fractions_are_preserved() -> None:
    reason = "needs-a-human-look-because-of-reason-7"
    terms = [_ratio("p", 1, 1, 2), _ratio("n", -1, 1, 3)]
    probability, details = _one(_record("proposal", terms, reason=reason))

    assert reason in list(_strings(details))
    assert "proposal" in list(_values_for_key(details, "outcome"))
    assert POLICY_ID in list(_values_for_key(details, "policy_id"))
    for exact in (Fraction(1, 4), Fraction(1, 9), Fraction(41, 72)):
        assert _carries_fraction(details, exact)
    assert probability == float(Fraction(41, 72))


# ---------------------------------------------------------------------------
# arbitrary-size whole numbers are exact
# ---------------------------------------------------------------------------


def test_integers_far_beyond_float_range_are_exact() -> None:
    big = 10**600
    probability, details = _one(
        _record(
            "proposal",
            [
                _term("big-positive", 1, big, 2 * big, 2 * big),  # exactly 1/4
                _term("big-negative", -1, big, 4 * big, 4 * big),  # exactly 1/16
            ],
        )
    )
    assert probability == float(_grade(Fraction(1, 4), Fraction(1, 16)))
    assert _carries_fraction(details, Fraction(1, 4))
    assert _carries_fraction(details, Fraction(1, 16))


def test_support_just_below_one_by_four_hundred_digits_stays_interior() -> None:
    n = 10**400
    probability, details = _one(_record("proposal", [_term("almost", 1, n - 1, n, n)]))
    support = Fraction((n - 1) ** 2, n * n)
    assert support != 1
    assert probability == math.nextafter(1.0, 0.0)  # float rounds to 1.0, kept interior
    assert 0.0 < probability < 1.0
    assert _carries_fraction(details, support)  # the exactness survives in details


def test_grade_that_underflows_to_zero_is_kept_interior_not_clipped_by_a_band() -> None:
    n = 10**400
    positive = _term("tiny", 1, 1, n, n)  # 10**-800
    negative = _term("almost", -1, n - 1, n, n)
    grade = _grade(Fraction(1, n * n), Fraction((n - 1) ** 2, n * n))
    assert grade == Fraction(1, n)

    probability, details = _one(_record("proposal", [positive, negative]))

    assert float(grade) == 0.0  # the premise: plain float rounding would be zero
    assert probability == math.nextafter(0.0, 1.0)
    assert _carries_fraction(details, grade)


def test_cosine_exactly_one_is_allowed_at_the_cauchy_boundary() -> None:
    n = 10**500 + 7
    probability, _ = _one(_record("proposal", [_term("same", 1, n, n, n)]))
    assert probability == math.nextafter(1.0, 0.0)


# ---------------------------------------------------------------------------
# malformed input is rejected with a named, nonempty code
# ---------------------------------------------------------------------------


def _assert_rejected(records: object, function=readout_study) -> None:
    with pytest.raises(ReadoutError) as caught:
        function(records)  # type: ignore[arg-type]
    assert isinstance(caught.value.code, str)
    assert caught.value.code.strip()


def _bad_terms(**overrides) -> dict:
    row = _ratio("bad", 1, 1, 2)
    row["terms"].update(overrides)
    return row


def _without(key: str) -> dict:
    row = _ratio("bad", 1, 1, 2)
    del row["terms"][key]
    return row


MALFORMED_ROWS = {
    "missing_dot": _without("dot"),
    "missing_left_norm": _without("left_norm_sq"),
    "missing_right_norm": _without("right_norm_sq"),
    "bool_dot": _bad_terms(dot=True),
    "bool_left_norm": _bad_terms(left_norm_sq=True),
    "bool_right_norm": _bad_terms(right_norm_sq=True),
    "fractional_dot": _bad_terms(dot=0.5),
    "string_dot": _bad_terms(dot="1"),
    "none_norm": _bad_terms(left_norm_sq=None),
    "negative_dot": _bad_terms(dot=-1),
    "negative_left_norm": _bad_terms(left_norm_sq=-4),
    "negative_right_norm": _bad_terms(right_norm_sq=-4),
    "zero_left_norm": _bad_terms(dot=0, left_norm_sq=0),
    "zero_right_norm": _bad_terms(dot=0, right_norm_sq=0),
    "cauchy_violation": _term("bad", 1, 3, 1, 1),
    "cauchy_violation_by_one_in_400_digits": _term(
        "bad", 1, 10**400 + 1, 10**400, 10**400
    ),
    "terms_not_a_mapping": {"case_id": "bad", "call": 1, "terms": [1, 1, 1]},
    "terms_none": {"case_id": "bad", "call": 1, "terms": None},
    "terms_absent": {"case_id": "bad", "call": 1},
    "call_zero": _term("bad", 0, 1, 2),
    "call_two": _term("bad", 2, 1, 2),
    "call_bool": _term("bad", True, 1, 2),
    "call_string": _term("bad", "1", 1, 2),
    "call_none": _term("bad", None, 1, 2),
    "case_id_none": _term(None, 1, 1, 2),
    "row_not_a_mapping": "not-a-row",
}


@pytest.mark.parametrize("name", sorted(MALFORMED_ROWS))
@pytest.mark.parametrize("function", [readout_study, probabilities_for_study])
def test_malformed_comparable_rows_are_rejected_for_the_whole_study(
    name: str, function
) -> None:
    good = _ratio("good", -1, 1, 3)
    _assert_rejected(
        _study(**{LABEL: _record("proposal", [good, MALFORMED_ROWS[name]])}), function
    )


def test_a_malformed_row_is_rejected_even_beside_a_perfectly_good_label() -> None:
    records = _study(
        **{
            OTHER_LABEL: _record("present"),
            LABEL: _record("proposal", [MALFORMED_ROWS["negative_dot"]]),
        }
    )
    _assert_rejected(records)


@pytest.mark.parametrize("bad", [{"p": 1}, "rows", None, 7])
def test_case_terms_must_be_a_list_of_rows(bad: object) -> None:
    record = _record("proposal")
    record["case_terms"] = bad
    _assert_rejected(_study(**{LABEL: record}))


@pytest.mark.parametrize("bad", [[True], [0], [2], ["1"], [1.0, None]])
def test_vetoed_answers_must_be_signed_digits(bad: list) -> None:
    record = _record("proposal", [_ratio("p", 1, 1, 2)])
    record["vetoed_answers"] = bad
    _assert_rejected(_study(**{LABEL: record}))


def test_the_study_must_contain_exactly_the_twelve_official_labels() -> None:
    complete = _study()
    assert len(complete) == len(LABELS) == 12

    missing = dict(complete)
    del missing[LABELS[-1]]
    _assert_rejected(missing)
    _assert_rejected(missing, probabilities_for_study)

    extra = dict(complete)
    extra["Not A Condition"] = _record("absent")
    _assert_rejected(extra)
    _assert_rejected(extra, probabilities_for_study)

    _assert_rejected({})
    _assert_rejected(None)
    _assert_rejected(list(complete.values()))


@pytest.mark.parametrize("bad", [None, "present", 1, ["present"]])
def test_each_label_record_must_be_a_mapping(bad: object) -> None:
    _assert_rejected(_study(**{LABEL: bad}))


@pytest.mark.parametrize("bad", ["", "bogus", "PRESENT-ish", 1, True, None])
def test_unknown_or_missing_outcome_is_rejected(bad: object) -> None:
    record = _record("proposal")
    record["outcome"] = bad
    _assert_rejected(_study(**{LABEL: record}))

    without = _record("proposal")
    del without["outcome"]
    _assert_rejected(_study(**{LABEL: without}))


def test_readout_module_exposes_only_the_documented_public_names() -> None:
    for name in (
        "POLICY_ID",
        "ReadoutError",
        "readout_study",
        "probabilities_for_study",
    ):
        assert hasattr(readout, name)
