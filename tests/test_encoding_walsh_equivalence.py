from __future__ import annotations

import numpy as np
import pytest

from knee.encoding.carrier import (
    ROW_WIDTH,
    CarrierError,
    CarrierOverflow,
    HadamardCarrier,
    _basis,
    _fwht,
    _permutation,
)


def test_fwht_matches_dense_left_and_right_for_every_basis_row():
    basis = _basis().astype(np.int64)
    for row in range(ROW_WIDTH):
        unit = np.zeros(ROW_WIDTH, dtype=np.int64)
        unit[row] = 1
        assert np.array_equal(_fwht(unit), basis[row])
        assert np.array_equal(_fwht(basis[row]), ROW_WIDTH * unit)


def test_seeded_permutations_and_dense_encoder_reference_match_exactly():
    carrier = HadamardCarrier.from_banks(("a", "b", "c", "d"))
    basis = _basis()
    rng = np.random.default_rng(49281)
    counts = rng.integers(0, 24, size=(len(carrier.banks), ROW_WIDTH), dtype=np.int64)
    actual = carrier.encode(counts)
    expected = np.zeros_like(actual)
    for seed in range(len(carrier.banks)):
        permuted = np.zeros(ROW_WIDTH, dtype=np.int64)
        permuted[_permutation(seed)] = counts[seed]
        expected[seed] = permuted @ basis
    assert np.array_equal(actual, expected)
    assert np.array_equal(carrier.decode(actual), counts)


def test_adversarial_signed_int32_decoder_matches_dense_reference():
    carrier = HadamardCarrier.from_banks(("a", "b"))
    rng = np.random.default_rng(29)
    encoded = rng.integers(
        np.iinfo(np.int32).min,
        np.iinfo(np.int32).max,
        size=(2, ROW_WIDTH),
        dtype=np.int32,
    )
    basis = _basis().astype(np.int64)
    for bank in range(2):
        expected = basis @ encoded[bank].astype(np.int64)
        assert np.array_equal(_fwht(encoded[bank]), expected)
    with pytest.raises(CarrierError):
        carrier.decode(encoded)


def test_object_integer_transform_is_exact_and_overflow_remains_named():
    huge = np.array([2**100 if i == 17 else 0 for i in range(ROW_WIDTH)], dtype=object)
    expected = np.asarray(huge, dtype=object) @ _basis().astype(object)
    assert np.array_equal(_fwht(huge), expected)
    carrier = HadamardCarrier.from_banks(("x",))
    counts = np.zeros((1, ROW_WIDTH), dtype=object)
    counts[0, 17] = 2**100
    with pytest.raises(CarrierOverflow, match="exceeds int32"):
        carrier.encode(counts)


def test_non_integral_or_wrong_width_private_transform_rejects_shape():
    with pytest.raises(CarrierError, match="shape"):
        _fwht(np.zeros(ROW_WIDTH - 1, dtype=np.int64))


def test_int32_boundary_bundle_round_trips_exactly():
    carrier = HadamardCarrier.from_banks(("x",))
    counts = np.zeros((1, ROW_WIDTH), dtype=np.int64)
    counts[0, 0] = np.iinfo(np.int32).max
    encoded = carrier.encode(counts)
    assert encoded[0].min() == -np.iinfo(np.int32).max
    assert encoded[0].max() == np.iinfo(np.int32).max
    assert np.array_equal(carrier.decode(encoded), counts)
