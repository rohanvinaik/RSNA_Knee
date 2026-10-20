from dataclasses import replace
from typing import cast

import pytest

from knee.encoding.counts import (
    BankLayout,
    CountBundle,
    CountCode,
    CountLayout,
    add_counts,
    compare_cosine_pairs,
    cosine_reaches_level,
    cosine_terms,
    subtract_counts,
)


def layout() -> CountLayout:
    return CountLayout(
        "layout-v1", "carrier-v1", (BankLayout("light", 3), BankLayout("depth", 2))
    )


def bundle(light: tuple[int, int, int], depth: tuple[int, int] = (0, 0)) -> CountBundle:
    return CountBundle(layout(), (light, depth))


def test_addition_is_order_independent_and_subtraction_undoes_it() -> None:
    a = bundle((1, 2, 0), (3, 0))
    b = bundle((4, 0, 1), (0, 5))
    c = bundle((0, 7, 2), (1, 1))

    ab = add_counts(a, b)
    bc = add_counts(b, c)
    assert ab.code is CountCode.OK and ab.bundle is not None
    assert bc.code is CountCode.OK and bc.bundle is not None
    left = add_counts(ab.bundle, c)
    right = add_counts(a, bc.bundle)
    assert left.code is right.code is CountCode.OK
    combined = left.bundle
    combined_other_order = right.bundle
    assert combined is not None and combined_other_order is not None
    assert combined == combined_other_order

    undone = subtract_counts(combined, c)
    assert undone.code is CountCode.OK
    assert undone.bundle == ab.bundle


def test_subtraction_underflow_is_named() -> None:
    result = subtract_counts(bundle((0, 1, 0)), bundle((0, 2, 0)))
    assert result.code is CountCode.UNDERFLOW
    assert result.bundle is None


def test_large_products_use_python_integer_arithmetic() -> None:
    n = 1 << 80
    left = bundle((n, n + 1, 0))
    right = bundle((n + 2, n, 0))
    result = cosine_reaches_level(left, right, ("light",), numerator=1, denominator=2)
    assert result.code is CountCode.REACHES
    assert result.terms is not None
    assert result.terms.dot > (1 << 64)
    assert result.terms.left_norm_sq > (1 << 64)
    assert result.terms.dot * result.terms.dot > (1 << 64)


def test_level_boundary_is_inclusive_and_exact() -> None:
    # (3, 4, 0) against (1, 0, 0) has cosine exactly 3/5.
    left = bundle((3, 4, 0))
    right = bundle((1, 0, 0))
    at_boundary = cosine_reaches_level(
        left, right, ("light",), numerator=3, denominator=5
    )
    above_boundary = cosine_reaches_level(
        left, right, ("light",), numerator=4, denominator=5
    )
    assert at_boundary.code is CountCode.REACHES
    assert above_boundary.code is CountCode.SHORT


def test_opposite_digits_and_middle_are_distinct_rows() -> None:
    # The three entries stand for -1, 0, +1 rows. Opposite counts do not cancel
    # into silence: the middle-only profile has a real norm and a zero dot.
    mixed = bundle((9, 0, 9))
    middle = bundle((0, 18, 0))
    result = cosine_reaches_level(mixed, middle, ("light",), numerator=0, denominator=1)
    assert result.code is CountCode.REACHES
    assert result.terms is not None
    assert result.terms.dot == 0
    assert result.terms.left_norm_sq == 162
    assert result.terms.right_norm_sq == 324
    above_zero = cosine_reaches_level(
        mixed, middle, ("light",), numerator=1, denominator=10
    )
    assert above_zero.code is CountCode.SHORT


def test_silent_bank_is_omitted_from_both_norms() -> None:
    left = bundle((2, 0, 0), (0, 0))
    right = bundle((3, 0, 0), (5, 0))
    result = cosine_terms(left, right, ("light", "depth"))
    assert result.code is CountCode.OK
    assert result.terms is not None
    assert result.terms.included_banks == ("light",)
    assert result.terms.dot == 6
    assert result.terms.left_norm_sq == 4
    assert result.terms.right_norm_sq == 9


def test_all_silent_selected_banks_are_silent_not_short() -> None:
    result = cosine_reaches_level(
        bundle((0, 0, 0)), bundle((1, 0, 0)), ("depth",), numerator=0, denominator=1
    )
    assert result.code is CountCode.SILENT
    assert result.terms is None


def test_incompatible_layout_or_carrier_is_rejected() -> None:
    source = bundle((1, 2, 3))
    other_layout = replace(layout(), layout_id="layout-v2")
    other = CountBundle(other_layout, source.counts)
    other_carrier = CountBundle(
        replace(layout(), carrier_id="carrier-v2"), source.counts
    )
    assert add_counts(source, other).code is CountCode.IDENTITY_MISMATCH
    assert (
        cosine_terms(source, other_carrier, ("light",)).code
        is CountCode.IDENTITY_MISMATCH
    )


@pytest.mark.parametrize(
    "bad",
    [
        None,
        CountBundle(layout(), ((1, -1, 0), (0, 0))),
        CountBundle(layout(), cast(tuple[tuple[int, ...], ...], ((1, 0.5, 0), (0, 0)))),
        CountBundle(layout(), ((True, 0, 0), (0, 0))),
        CountBundle(layout(), ((1, 0), (0, 0))),
        CountBundle(layout(), ((1, 0, 0),)),
    ],
)
def test_null_and_malformed_bundles_are_invalid(bad: object) -> None:
    malformed = cast(CountBundle, bad)
    assert add_counts(malformed, bundle((0, 0, 0))).code is CountCode.INVALID_INPUT
    assert (
        cosine_terms(malformed, bundle((0, 0, 0)), ("light",)).code
        is CountCode.INVALID_INPUT
    )


def test_invalid_selection_and_level_are_named() -> None:
    a = bundle((1, 0, 0))
    assert cosine_terms(a, a, ("unknown",)).code is CountCode.INVALID_INPUT
    assert cosine_terms(a, a, ("light", "light")).code is CountCode.INVALID_INPUT
    assert (
        cosine_reaches_level(a, a, ("light",), numerator=True, denominator=1).code
        is CountCode.INVALID_INPUT
    )
    assert (
        cosine_reaches_level(a, a, ("light",), numerator=1, denominator=0).code
        is CountCode.INVALID_INPUT
    )
    assert (
        cosine_reaches_level(a, a, ("light",), numerator=2, denominator=1).code
        is CountCode.INVALID_INPUT
    )


def test_pairwise_cosine_order_has_exact_tie_and_silent_results() -> None:
    query = bundle((3, 0, 0))
    same = bundle((5, 0, 0))
    orthogonal = bundle((0, 5, 0))
    assert (
        compare_cosine_pairs(query, same, orthogonal, ("light",)).code
        is CountCode.FIRST_NEARER
    )
    assert compare_cosine_pairs(query, same, same, ("light",)).code is CountCode.TIE
    absent = bundle((0, 0, 0))
    assert (
        compare_cosine_pairs(query, absent, same, ("light",)).code is CountCode.SILENT
    )
