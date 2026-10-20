from __future__ import annotations

from fractions import Fraction

import numpy as np

from knee.encoding.carrier import HadamardCarrier
from knee.encoding.counts import (
    BankLayout,
    CountBundle,
    CountCode,
    CountLayout,
    add_counts,
    compare_cosine_pairs,
    cosine_reaches_level,
    cosine_terms,
)
from knee.encoding.handoff import encode_observation
from knee.encoding.places import (
    BankSpec,
    LayoutSpec,
    MetricKind,
    MetricSpec,
    NumericReference,
    PlaceReading,
    compile_layout,
    encode_places,
)
from knee.receipt import digest


def _bundle(layout: CountLayout, rows: tuple[tuple[int, ...], ...]) -> CountBundle:
    return CountBundle(layout, rows)


def test_shared_bank_count_cosine_matches_exact_dense_carrier_products() -> None:
    rng = np.random.default_rng(20261020)
    banks = ("a", "b", "c", "d")
    carrier = HadamardCarrier.from_banks(banks)
    layout = CountLayout(
        "property-layout-v1",
        carrier.identity,
        tuple(BankLayout(name, 512) for name in banks),
    )
    for _ in range(20):
        left = rng.integers(0, 5, size=(len(banks), 512), dtype=np.int64)
        right = rng.integers(0, 5, size=(len(banks), 512), dtype=np.int64)
        # Exercise the pairwise-silence rule: a bank active on only one side is
        # absent from both norms and the dot product.
        left[1] = 0
        right[2] = 0
        left_bundle = _bundle(layout, tuple(tuple(map(int, row)) for row in left))
        right_bundle = _bundle(layout, tuple(tuple(map(int, row)) for row in right))
        selected = ("a", "b", "c", "d")
        exact = cosine_terms(left_bundle, right_bundle, selected)
        assert exact.code is CountCode.OK and exact.terms is not None

        left_dense = carrier.encode(left)
        right_dense = carrier.encode(right)
        included = [
            index
            for index in range(len(banks))
            if np.any(left[index]) and np.any(right[index])
        ]
        left_vectors = left_dense[included].astype(np.int64)
        right_vectors = right_dense[included].astype(np.int64)
        dense_dot = sum(
            int(a) * int(b)
            for a, b in zip(left_vectors.flat, right_vectors.flat, strict=True)
        )
        dense_left_norm = sum(int(value) ** 2 for value in left_vectors.flat)
        dense_right_norm = sum(int(value) ** 2 for value in right_vectors.flat)
        assert dense_dot == 512 * exact.terms.dot
        assert dense_left_norm == 512 * exact.terms.left_norm_sq
        assert dense_right_norm == 512 * exact.terms.right_norm_sq

        for numerator, denominator in ((0, 1), (1, 3), (1, 1)):
            reached = cosine_reaches_level(
                left_bundle,
                right_bundle,
                selected,
                numerator=numerator,
                denominator=denominator,
            )
            assert reached.terms == exact.terms
            lhs = Fraction(dense_dot * dense_dot, dense_left_norm * dense_right_norm)
            rhs = Fraction(numerator * numerator, denominator * denominator)
            assert reached.code is (
                CountCode.REACHES if lhs >= rhs else CountCode.SHORT
            )


def test_cosine_pair_cross_products_match_exact_fraction_order_above_float_range() -> (
    None
):
    layout = CountLayout("huge-v1", "carrier", (BankLayout("shared", 3),))
    base = 1 << 80
    query = _bundle(layout, ((base + 2, base + 1, base),))
    first = _bundle(layout, ((base + 4, base, base + 1),))
    second = _bundle(layout, ((base + 2, base + 2, base + 1),))
    actual = compare_cosine_pairs(query, first, second, ("shared",))
    first_terms = cosine_terms(query, first, ("shared",)).terms
    second_terms = cosine_terms(query, second, ("shared",)).terms
    assert first_terms is not None and second_terms is not None
    first_cosine_sq = Fraction(
        first_terms.dot**2, first_terms.left_norm_sq * first_terms.right_norm_sq
    )
    second_cosine_sq = Fraction(
        second_terms.dot**2, second_terms.left_norm_sq * second_terms.right_norm_sq
    )
    expected = (
        CountCode.FIRST_NEARER
        if first_cosine_sq > second_cosine_sq
        else CountCode.SECOND_NEARER
        if first_cosine_sq < second_cosine_sq
        else CountCode.TIE
    )
    assert actual.code is expected


def test_place_aggregate_is_independent_of_place_order_and_carrier_matches_bundle() -> (
    None
):
    carrier = HadamardCarrier.from_banks(("appearance",))
    layout = compile_layout(
        LayoutSpec(
            "property-place-v1",
            carrier.identity,
            (
                BankSpec(
                    "appearance",
                    "profile",
                    (
                        MetricSpec("signal", MetricKind.DIGIT),
                        MetricSpec("state", MetricKind.WORDS, ("left", "right")),
                    ),
                ),
            ),
        )
    )
    assert layout is not None
    reference = NumericReference(
        layout.fingerprint, "appearance", "signal", "ref", "source", "unit", -1, 1
    )
    values = np.array([-2.0, -1.0, 0.0, 2.0, np.nan])
    words = np.array(["left", "right", "left", "right", "left"])
    available = np.array([True, True, True, True, False])
    full = encode_places(
        layout,
        {
            ("appearance", "signal"): PlaceReading(
                "appearance", "signal", values, available
            ),
            ("appearance", "state"): PlaceReading(
                "appearance", "state", words, available
            ),
        },
        {("appearance", "signal"): reference},
    )
    assert full.bundle is not None

    fragments = []
    for index in range(values.size):
        fragment = encode_places(
            layout,
            {
                ("appearance", "signal"): PlaceReading(
                    "appearance",
                    "signal",
                    values[index : index + 1],
                    available[index : index + 1],
                ),
                ("appearance", "state"): PlaceReading(
                    "appearance",
                    "state",
                    words[index : index + 1],
                    available[index : index + 1],
                ),
            },
            {("appearance", "signal"): reference},
        )
        assert fragment.bundle is not None
        fragments.append(fragment.bundle)
    forward = fragments[0]
    for fragment in fragments[1:]:
        added = add_counts(forward, fragment)
        assert added.code is CountCode.OK and added.bundle is not None
        forward = added.bundle
    reverse = fragments[-1]
    for fragment in reversed(fragments[:-1]):
        added = add_counts(reverse, fragment)
        assert added.code is CountCode.OK and added.bundle is not None
        reverse = added.bundle
    assert forward == reverse == full.bundle

    carrier = HadamardCarrier.from_banks(("appearance",))
    dense = carrier.encode(np.asarray(full.bundle.counts, dtype=np.int64))
    left, right = dense[0].astype(np.int64), dense[0].astype(np.int64)
    count_norm = sum(count * count for count in full.bundle.counts[0])
    assert sum(int(a) * int(b) for a, b in zip(left, right, strict=True)) == (
        512 * count_norm
    )


def test_handoff_counts_only_available_native_places_inside_retained_window() -> None:
    layout = compile_layout(
        LayoutSpec(
            "handoff-v1",
            "handoff-carrier-v1",
            (BankSpec("signal", "profile", (MetricSpec("value", MetricKind.DIGIT),)),),
        )
    )
    assert layout is not None
    support = np.zeros((3, 4), dtype=np.bool_)
    support[0, 0] = True
    support[1, 1] = True
    support[2, 2] = True
    value_crop = np.array([[7.0, 8.0], [9.0, 10.0]])
    available_crop = np.array([[True, True], [False, True]])
    window = np.array([1, 3, 0, 2], dtype=np.int32)
    arrays = {
        "support": support,
        "value": value_crop,
        "available": available_crop,
        "window": window,
    }
    record = {
        "artifact": "study/series.npz.xz",
        "series_uid": "series",
        "slice_index": 4,
        "view": ["Axial", "1", "1"],
        "plane_frame": {"origin_lps": [1.0, 2.0, 3.0]},
        "arrays": {name: {"digest": digest(array)} for name, array in arrays.items()},
    }
    observation = {
        "provenance": "native",
        "kind": "reading",
        "artifact": record["artifact"],
        "series_uid": "series",
        "view": ["Axial", "1", "1"],
        "slices": [4],
        "support": "support",
        "row": None,
        "label": None,
        "count": 3,
    }
    reference = NumericReference(
        layout.fingerprint, "signal", "value", "ref", "source", "unit", 8, 9
    )
    encoded = encode_observation(
        record,
        observation,
        arrays,
        layout,
        (
            {
                "bank": "signal",
                "metric": "value",
                "value": "value",
                "available": "available",
                "window": "window",
            },
        ),
        {("signal", "value"): reference},
    )
    assert encoded.encoding is not None
    assert encoded.points_rc is not None
    assert encoded.points_rc.tolist() == [[0, 0], [1, 1], [2, 2]]
    assert encoded.encoding.metrics[0].row_codes.tolist() == [-1, 1, -1]
    assert encoded.encoding.bundle is not None
    assert encoded.encoding.bundle.counts[0][:3] == (0, 1, 0)
    assert encoded.metadata["plane_frame"] == record["plane_frame"]
