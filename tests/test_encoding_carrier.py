from __future__ import annotations

import numpy as np
import pytest

from knee.encoding.carrier import (
    ROW_WIDTH,
    CarrierError,
    CarrierOverflow,
    HadamardCarrier,
)

BANKS = ("basement", "shape", "region", "motion")


def test_all_bank_rows_match_seeded_sylvester_permutations_and_are_orthogonal():
    carrier = HadamardCarrier.from_banks(BANKS)
    dimensions = np.arange(ROW_WIDTH, dtype=np.uint16)
    for seed, _name in enumerate(carrier.banks):
        order = np.random.default_rng(seed).permutation(ROW_WIDTH)
        rows = np.where(
            (
                np.bitwise_count(order[:, None].astype(np.uint16) & dimensions[None, :])
                & 1
            )
            == 0,
            1,
            -1,
        ).astype(np.int64)
        assert np.array_equal(
            rows @ rows.T, ROW_WIDTH * np.eye(ROW_WIDTH, dtype=np.int64)
        )
        # Check the actual encoder against the independently constructed basis;
        # a matching encode/decode mistake must not pass only by round-tripping.
        for row in (0, 13, 511):
            single = np.zeros((len(BANKS), ROW_WIDTH), dtype=np.int64)
            single[seed, row] = 1
            actual = carrier.encode(single)
            assert np.array_equal(actual[seed], rows[row])
            assert not np.delete(actual, seed, axis=0).any()
    assert len(carrier.identity.split(":", maxsplit=1)[1]) == 64


def test_round_trip_many_rows_repeated_counts_and_addition_equivalence():
    carrier = HadamardCarrier.from_banks(BANKS)
    left = np.zeros((len(BANKS), ROW_WIDTH), dtype=np.int64)
    right = np.zeros_like(left)
    left[0, 0], left[0, 13], left[1, 511] = 3, 9, 2
    right[0, 0], right[2, 200], right[3, 44] = 4, 7, 1
    encoded_left = carrier.encode(left)
    encoded_right = carrier.encode(right)
    summed_counts = left + right
    summed_vector = carrier.encode(summed_counts)
    assert np.array_equal(summed_vector, encoded_left.astype(np.int64) + encoded_right)
    assert np.array_equal(carrier.decode(summed_vector), summed_counts)


def test_layout_names_seed_order_and_real_permutation_fingerprints_are_in_identity():
    first = HadamardCarrier.from_banks(("a", "b"))
    reordered = HadamardCarrier.from_banks(("b", "a"))
    extended = HadamardCarrier.from_banks(("a", "b", "c"))
    assert first.identity != reordered.identity
    assert first.identity != extended.identity
    assert first.identity == HadamardCarrier.from_banks(("a", "b")).identity


def test_non_hadamard_vector_and_fractional_inverse_are_refused():
    carrier = HadamardCarrier.from_banks(("x",))
    bad = np.zeros((1, ROW_WIDTH), dtype=np.int32)
    bad[0, 0] = 1
    with pytest.raises(CarrierError, match="integral Hadamard"):
        carrier.decode(bad)
    nonnegative_but_nonbundle = np.ones((1, ROW_WIDTH), dtype=np.int32)
    # all ones is a valid row-0 vector, hence exact decode is allowed
    assert carrier.decode(nonnegative_but_nonbundle)[0].sum() == 1


def test_negative_decoded_counts_and_bad_input_types_are_refused():
    carrier = HadamardCarrier.from_banks(("x",))
    negative_bundle = carrier.encode(np.eye(1, ROW_WIDTH, 0, dtype=np.int64))
    with pytest.raises(CarrierError, match="negative row count"):
        carrier.decode(-negative_bundle)
    with pytest.raises(CarrierError, match="integer dtype"):
        carrier.encode(np.zeros((1, ROW_WIDTH), dtype=np.float64))
    with pytest.raises(CarrierError, match="integer dtype"):
        carrier.encode(np.zeros((1, ROW_WIDTH), dtype=bool))
    with pytest.raises(CarrierError, match="dtype int32"):
        carrier.decode(np.zeros((1, ROW_WIDTH), dtype=np.int64))


def test_overflow_is_named_and_never_wraps():
    carrier = HadamardCarrier.from_banks(("x",))
    counts = np.zeros((1, ROW_WIDTH), dtype=np.uint64)
    counts[0, 0] = np.iinfo(np.uint64).max
    with pytest.raises(CarrierOverflow):
        carrier.encode(counts)
    counts = np.zeros((1, ROW_WIDTH), dtype=np.int64)
    counts[0, 0] = np.iinfo(np.int32).max + 1
    with pytest.raises(CarrierOverflow, match="exceeds int32"):
        carrier.encode(counts)


def test_python_integer_tables_are_exact_until_vector_range_is_exceeded():
    carrier = HadamardCarrier.from_banks(("x",))
    small = np.zeros((1, ROW_WIDTH), dtype=object)
    small[0, 17] = 7
    encoded = carrier.encode(small)
    assert encoded.dtype == np.int32
    assert carrier.decode(encoded)[0, 17] == 7

    huge = np.zeros((1, ROW_WIDTH), dtype=object)
    huge[0, 0] = 2**100
    with pytest.raises(CarrierOverflow, match="exceeds int32"):
        carrier.encode(huge)

    malformed = np.zeros((1, ROW_WIDTH), dtype=object)
    malformed[0, 0] = True
    with pytest.raises(CarrierError, match="non-boolean integers"):
        carrier.encode(malformed)


def test_zero_banks_are_explicitly_supported_as_empty_silent_carrier():
    carrier = HadamardCarrier.from_banks(())
    empty = np.zeros((0, ROW_WIDTH), dtype=np.int64)
    encoded = carrier.encode(empty)
    assert encoded.shape == (0, ROW_WIDTH) and encoded.dtype == np.int32
    assert carrier.decode(encoded).shape == empty.shape
    assert carrier.identity.startswith("hadamard-counts-v1:")


def test_silent_banks_remain_zero_while_other_bank_rows_are_decoded():
    carrier = HadamardCarrier.from_banks(("silent", "speaking"))
    counts = np.zeros((2, ROW_WIDTH), dtype=np.int64)
    counts[1, 255] = 5
    encoded = carrier.encode(counts)
    assert not encoded[0].any()
    assert np.array_equal(carrier.decode(encoded), counts)


def test_duplicate_or_empty_bank_names_are_refused():
    for names in (("a", "a"), ("",), ("  ",), "abc"):
        with pytest.raises(CarrierError):
            HadamardCarrier.from_banks(names)
