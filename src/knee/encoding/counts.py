"""Exact arithmetic for typed row-count bundles.

This module deliberately contains no domain profile, threshold, vector carrier,
or interpretation.  Callers supply a versioned layout and the banks a question
reads.  The arithmetic follows the count-table reference: Python integers are
the widened accumulator, and no floating-point value participates in a result.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from enum import StrEnum


class CountCode(StrEnum):
    OK = "ok"
    REACHES = "reaches"
    SHORT = "short"
    SILENT = "silent"
    FIRST_NEARER = "first_nearer"
    SECOND_NEARER = "second_nearer"
    TIE = "tie"
    INVALID_INPUT = "invalid_input"
    IDENTITY_MISMATCH = "identity_mismatch"
    UNDERFLOW = "underflow"


@dataclass(frozen=True, slots=True)
class BankLayout:
    """A named bank and its exact row cardinality."""

    name: str
    row_count: int


@dataclass(frozen=True, slots=True)
class CountLayout:
    """Versioned identities and the ordered banks in one count-table layout."""

    layout_id: str
    carrier_id: str
    banks: tuple[BankLayout, ...]


@dataclass(frozen=True, slots=True)
class CountBundle:
    """Nonnegative whole-number row counts, one tuple per layout bank."""

    layout: CountLayout
    counts: tuple[tuple[int, ...], ...]


@dataclass(frozen=True, slots=True)
class CountResult:
    code: CountCode
    bundle: CountBundle | None = None


@dataclass(frozen=True, slots=True)
class CosineTerms:
    """Exact terms for one cosine; common silent banks are omitted."""

    dot: int
    left_norm_sq: int
    right_norm_sq: int
    included_banks: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class CosineResult:
    code: CountCode
    terms: CosineTerms | None = None


def _is_plain_int(value: object) -> bool:
    return isinstance(value, int) and not isinstance(value, bool)


def _valid_layout(layout: object) -> bool:
    if not isinstance(layout, CountLayout):
        return False
    if not isinstance(layout.layout_id, str) or not layout.layout_id:
        return False
    if not isinstance(layout.carrier_id, str) or not layout.carrier_id:
        return False
    if not isinstance(layout.banks, tuple) or not layout.banks:
        return False
    names: set[str] = set()
    for bank in layout.banks:
        if not isinstance(bank, BankLayout):
            return False
        if not isinstance(bank.name, str) or not bank.name or bank.name in names:
            return False
        if not _is_plain_int(bank.row_count) or bank.row_count <= 0:
            return False
        names.add(bank.name)
    return True


def _valid_bundle(bundle: object) -> bool:
    if not isinstance(bundle, CountBundle) or not _valid_layout(bundle.layout):
        return False
    if not isinstance(bundle.counts, tuple) or len(bundle.counts) != len(
        bundle.layout.banks
    ):
        return False
    checked_rows: dict[int, tuple[int, ...]] = {}
    for bank_counts, bank in zip(bundle.counts, bundle.layout.banks, strict=True):
        if not isinstance(bank_counts, tuple) or len(bank_counts) != bank.row_count:
            return False
        if checked_rows.get(id(bank_counts)) is bank_counts:
            continue
        reusable = type(bank_counts) is tuple
        for count in bank_counts:
            if not _is_plain_int(count) or count < 0:
                return False
            reusable = reusable and type(count) is int
        if reusable:
            checked_rows[id(bank_counts)] = bank_counts
    return True


def _same_identity(left: CountBundle, right: CountBundle) -> bool:
    return left.layout == right.layout


def add_counts(left: CountBundle, right: CountBundle) -> CountResult:
    """Add two bundles exactly, independent of addition order."""
    if not _valid_bundle(left) or not _valid_bundle(right):
        return CountResult(CountCode.INVALID_INPUT)
    if not _same_identity(left, right):
        return CountResult(CountCode.IDENTITY_MISMATCH)
    summed = tuple(
        tuple(a + b for a, b in zip(left_bank, right_bank, strict=True))
        for left_bank, right_bank in zip(left.counts, right.counts, strict=True)
    )
    return CountResult(CountCode.OK, CountBundle(left.layout, summed))


def subtract_counts(left: CountBundle, right: CountBundle) -> CountResult:
    """Subtract exactly; a negative row count is a named underflow."""
    if not _valid_bundle(left) or not _valid_bundle(right):
        return CountResult(CountCode.INVALID_INPUT)
    if not _same_identity(left, right):
        return CountResult(CountCode.IDENTITY_MISMATCH)
    if any(
        a < b
        for left_bank, right_bank in zip(left.counts, right.counts, strict=True)
        for a, b in zip(left_bank, right_bank, strict=True)
    ):
        return CountResult(CountCode.UNDERFLOW)
    difference = tuple(
        tuple(a - b for a, b in zip(left_bank, right_bank, strict=True))
        for left_bank, right_bank in zip(left.counts, right.counts, strict=True)
    )
    return CountResult(CountCode.OK, CountBundle(left.layout, difference))


def _selected_indices(
    layout: CountLayout, selected_banks: Sequence[str]
) -> tuple[int, ...] | None:
    if isinstance(selected_banks, (str, bytes)):
        return None
    try:
        names = tuple(selected_banks)
    except TypeError:
        return None
    if any(not isinstance(name, str) for name in names) or len(set(names)) != len(
        names
    ):
        return None
    index = {bank.name: i for i, bank in enumerate(layout.banks)}
    if any(name not in index for name in names):
        return None
    return tuple(index[name] for name in names)


def cosine_terms(
    left: CountBundle,
    right: CountBundle,
    selected_banks: Sequence[str],
) -> CosineResult:
    """Build one cosine's exact dot and norms over the named shared banks."""
    if not _valid_bundle(left) or not _valid_bundle(right):
        return CosineResult(CountCode.INVALID_INPUT)
    if not _same_identity(left, right):
        return CosineResult(CountCode.IDENTITY_MISMATCH)
    selected = _selected_indices(left.layout, selected_banks)
    if selected is None:
        return CosineResult(CountCode.INVALID_INPUT)

    dot = left_norm_sq = right_norm_sq = 0
    included: list[str] = []
    for index in selected:
        left_bank = left.counts[index]
        right_bank = right.counts[index]
        # Silence is a bank-level absence, not a zero-valued negative vote.
        if not any(left_bank) or not any(right_bank):
            continue
        included.append(left.layout.banks[index].name)
        dot += sum(a * b for a, b in zip(left_bank, right_bank, strict=True))
        left_norm_sq += sum(a * a for a in left_bank)
        right_norm_sq += sum(b * b for b in right_bank)
    if not included:
        return CosineResult(CountCode.SILENT)
    return CosineResult(
        CountCode.OK,
        CosineTerms(dot, left_norm_sq, right_norm_sq, tuple(included)),
    )


def cosine_reaches_level(
    left: CountBundle,
    right: CountBundle,
    selected_banks: Sequence[str],
    *,
    numerator: int,
    denominator: int,
) -> CosineResult:
    """Classify one cosine against an explicit nonnegative rational level."""
    if not _is_plain_int(numerator) or numerator < 0:
        return CosineResult(CountCode.INVALID_INPUT)
    if not _is_plain_int(denominator) or denominator <= 0:
        return CosineResult(CountCode.INVALID_INPUT)
    if numerator > denominator:
        return CosineResult(CountCode.INVALID_INPUT)
    terms_result = cosine_terms(left, right, selected_banks)
    if terms_result.code is not CountCode.OK:
        return terms_result
    assert terms_result.terms is not None
    terms = terms_result.terms
    # Counts are nonnegative. This is the exact whole-number test from §13.2.
    reaches = denominator * denominator * terms.dot * terms.dot >= (
        numerator * numerator * terms.left_norm_sq * terms.right_norm_sq
    )
    code = CountCode.REACHES if reaches else CountCode.SHORT
    return CosineResult(code, terms)


def compare_cosine_pairs(
    query: CountBundle,
    first: CountBundle,
    second: CountBundle,
    selected_banks: Sequence[str],
) -> CosineResult:
    """Compare query-to-first and query-to-second cosines exactly.

    If either pair is silent, the comparison is silent; it is never treated as
    a losing or negative candidate.
    """
    first_result = cosine_terms(query, first, selected_banks)
    if first_result.code in (CountCode.INVALID_INPUT, CountCode.IDENTITY_MISMATCH):
        return first_result
    second_result = cosine_terms(query, second, selected_banks)
    if second_result.code in (CountCode.INVALID_INPUT, CountCode.IDENTITY_MISMATCH):
        return second_result
    if first_result.code is CountCode.SILENT or second_result.code is CountCode.SILENT:
        return CosineResult(CountCode.SILENT)
    assert first_result.terms is not None and second_result.terms is not None
    a = first_result.terms
    b = second_result.terms
    first_cross = a.dot * a.dot * b.left_norm_sq * b.right_norm_sq
    second_cross = b.dot * b.dot * a.left_norm_sq * a.right_norm_sq
    if first_cross > second_cross:
        code = CountCode.FIRST_NEARER
    elif first_cross < second_cross:
        code = CountCode.SECOND_NEARER
    else:
        code = CountCode.TIE
    return CosineResult(code)
