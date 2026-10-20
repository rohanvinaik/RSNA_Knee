from dataclasses import replace

import numpy as np

from knee.encoding.counts import CountCode, add_counts
from knee.encoding.places import (
    BankSpec,
    EncodingCode,
    LayoutSpec,
    MetricKind,
    MetricSpec,
    NumericReference,
    PlaceReading,
    _can_vectorize_digit_compare,
    _digit_row_codes,
    compile_layout,
    decode_count_names,
    encode_places,
)


def fixture_layout():
    spec = LayoutSpec(
        "schema-v1",
        "carrier-test-v1",
        (
            BankSpec(
                "appearance",
                "facet-a",
                (MetricSpec("light", MetricKind.DIGIT),),
            ),
            BankSpec(
                "context",
                "facet-b",
                (MetricSpec("route", MetricKind.WORDS, ("first", "search", "last")),),
            ),
        ),
    )
    compiled = compile_layout(spec)
    assert compiled is not None
    return spec, compiled


def reference(layout, *, low=-0.5, high=0.5):
    return NumericReference(
        layout.fingerprint,
        "appearance",
        "light",
        "ref-light-v1",
        "caller-authored source",
        "unit-test units",
        low,
        high,
    )


def reading(bank, metric, values, available=None):
    array = np.asarray(values)
    if available is None:
        available_array = np.ones(array.shape, dtype=np.bool_)
    else:
        available_array = np.asarray(available)
    return PlaceReading(bank, metric, array, available_array)


def test_digits_keep_opposite_rows_distinct_from_middle() -> None:
    _, layout = fixture_layout()
    values = np.array([-1.0, 0.0, 1.0])
    available = np.ones(3, dtype=np.bool_)
    authored_reference = reference(layout)
    result = encode_places(
        layout,
        {
            ("appearance", "light"): PlaceReading(
                "appearance", "light", values, available
            ),
            ("context", "route"): reading("context", "route", ["first"] * 3),
        },
        {("appearance", "light"): authored_reference},
    )
    assert result.status is EncodingCode.OK
    assert result.bundle is not None
    encoded = result.metrics[0]
    assert encoded.row_codes.tolist() == [0, 1, 2]
    assert not encoded.row_codes.flags.writeable
    assert encoded.source_values is values
    assert encoded.source_available is available
    assert encoded.reference is authored_reference
    assert result.bundle.counts[0][:3] == (1, 1, 1)
    assert len(result.bundle.counts[0]) == 512
    assert not any(result.bundle.counts[0][3:])

    middle_only = encode_places(
        layout,
        {
            ("appearance", "light"): reading("appearance", "light", [0.0, 0.0]),
            ("context", "route"): reading("context", "route", ["first"] * 2),
        },
        {("appearance", "light"): reference(layout)},
    )
    assert middle_only.bundle is not None
    assert middle_only.bundle.counts[0][:3] == (0, 2, 0)


def test_measured_zero_is_middle_but_unread_place_stays_silent() -> None:
    _, layout = fixture_layout()
    values = np.array([0.0, -900.0])
    available = np.array([True, False], dtype=np.bool_)
    result = encode_places(
        layout,
        {
            ("appearance", "light"): PlaceReading(
                "appearance", "light", values, available
            ),
            ("context", "route"): reading("context", "route", ["first"] * 2),
        },
        {("appearance", "light"): reference(layout)},
    )
    assert result.bundle is not None
    assert result.metrics[0].row_codes.tolist() == [1, -1]
    assert result.bundle.counts[0][:3] == (0, 1, 0)


def test_words_use_ordered_declared_rows_and_decode_names() -> None:
    _, layout = fixture_layout()
    word_values = np.array(["last", "first", "search", "first"])
    result = encode_places(
        layout,
        {
            ("appearance", "light"): reading(
                "appearance", "light", [0.0, 1.0, -1.0, 0.0]
            ),
            ("context", "route"): PlaceReading(
                "context", "route", word_values, np.ones(4, dtype=np.bool_)
            ),
        },
        {("appearance", "light"): reference(layout)},
    )
    assert result.bundle is not None
    route = result.metrics[1]
    assert route.row_codes.tolist() == [2, 0, 1, 0]
    assert result.bundle.counts[1][:3] == (2, 1, 1)
    assert len(result.bundle.counts[1]) == 512
    assert not any(result.bundle.counts[1][3:])
    ref_set = result.reference_set_fingerprint
    assert ref_set is not None
    names = decode_count_names(layout, result.bundle, ref_set)
    assert names is not None
    assert ("context", "facet-b", "route", "first", 2) in names
    assert ("appearance", "facet-a", "light", "-1", 1) in names


def test_word_outside_declared_values_is_invalid_not_a_negative_row() -> None:
    _, layout = fixture_layout()
    result = encode_places(
        layout,
        {
            ("appearance", "light"): reading("appearance", "light", [0.0]),
            ("context", "route"): reading("context", "route", ["unlisted"]),
        },
        {("appearance", "light"): reference(layout)},
    )
    assert result.status is EncodingCode.INVALID_INPUT
    assert result.bundle is None
    assert result.metrics[1].status is EncodingCode.INVALID_INPUT
    assert result.metrics[1].row_codes.tolist() == [-1]


def test_boolean_word_values_use_canonical_declared_rows_and_preserve_source() -> None:
    layout = compile_layout(
        LayoutSpec(
            "boolean-words-v1",
            "boolean-carrier-v1",
            (
                BankSpec(
                    "lens",
                    "profile",
                    (
                        MetricSpec(
                            "dark", MetricKind.WORDS, ("True", "False", "unused")
                        ),
                    ),
                ),
            ),
        )
    )
    assert layout is not None
    values = np.array([False, True, False, True], dtype=np.bool_)
    available = np.array([True, True, False, False], dtype=np.bool_)
    result = encode_places(
        layout,
        {("lens", "dark"): PlaceReading("lens", "dark", values, available)},
        {},
    )
    assert result.status is EncodingCode.OK
    assert result.bundle is not None
    encoded = result.metrics[0]
    assert encoded.row_codes.tolist() == [1, 0, -1, -1]
    assert encoded.row_names == ("True", "False", "unused")
    assert encoded.source_values is values
    assert encoded.source_values.dtype.kind == "b"
    assert encoded.source_available is available
    assert result.bundle.counts[0][:3] == (1, 1, 0)


def test_boolean_word_declaration_must_name_each_observed_value_only() -> None:
    layout = compile_layout(
        LayoutSpec(
            "boolean-word-subset-v1",
            "boolean-carrier-v1",
            (
                BankSpec(
                    "lens",
                    "profile",
                    (MetricSpec("dark", MetricKind.WORDS, ("True",)),),
                ),
            ),
        )
    )
    assert layout is not None
    values = np.array([False, True], dtype=np.bool_)
    available = np.array([False, True], dtype=np.bool_)
    result = encode_places(
        layout,
        {("lens", "dark"): PlaceReading("lens", "dark", values, available)},
        {},
    )
    assert result.status is EncodingCode.OK
    assert result.bundle is not None
    assert result.metrics[0].row_codes.tolist() == [-1, 0]

    missing_observed_word = encode_places(
        layout,
        {
            ("lens", "dark"): PlaceReading(
                "lens", "dark", values, np.ones(2, dtype=np.bool_)
            )
        },
        {},
    )
    assert missing_observed_word.status is EncodingCode.INVALID_INPUT
    assert missing_observed_word.bundle is None


def test_missing_reference_keeps_metric_unwritten_and_provenance_arrays() -> None:
    _, layout = fixture_layout()
    values = np.array([0.0, 1.0])
    available = np.ones(2, dtype=np.bool_)
    result = encode_places(
        layout,
        {
            ("appearance", "light"): PlaceReading(
                "appearance", "light", values, available
            ),
            ("context", "route"): PlaceReading(
                "context",
                "route",
                np.array(["first", "last"]),
                np.ones(2, dtype=np.bool_),
            ),
        },
        {},
    )
    assert result.status is EncodingCode.MISSING_REFERENCE
    assert result.bundle is not None
    assert result.metrics[0].status is EncodingCode.MISSING_REFERENCE
    assert result.metrics[0].row_codes.tolist() == [-1, -1]
    assert result.metrics[0].source_values is values
    assert result.metrics[0].source_available is available
    assert not any(result.bundle.counts[0])


def test_reference_identity_must_match_layout_bank_and_metric() -> None:
    _, layout = fixture_layout()
    mismatched = replace(reference(layout), layout_fingerprint="other-layout")
    result = encode_places(
        layout,
        {
            ("appearance", "light"): reading("appearance", "light", [0.0]),
            ("context", "route"): reading("context", "route", ["first"]),
        },
        {("appearance", "light"): mismatched},
    )
    assert result.status is EncodingCode.IDENTITY_MISMATCH
    assert result.bundle is None
    assert result.metrics[0].status is EncodingCode.IDENTITY_MISMATCH


def test_reference_set_identity_prevents_cross_reference_bundle_comparison() -> None:
    _, layout = fixture_layout()
    values = np.array([0.0, 1.0])
    readings = {
        ("appearance", "light"): reading("appearance", "light", values),
        ("context", "route"): reading("context", "route", ["first", "last"]),
    }
    first = encode_places(
        layout, readings, {("appearance", "light"): reference(layout)}
    )
    missing = encode_places(layout, readings, {})
    assert first.bundle is not None
    assert missing.bundle is not None
    assert add_counts(first.bundle, missing.bundle).code is CountCode.IDENTITY_MISMATCH
    original = reference(layout)
    variants = (
        replace(original, reference_id="other-authored-reference"),
        replace(original, source="other-source"),
        replace(original, units="other-units"),
        replace(original, low=-0.25),
        replace(original, high=0.75),
    )
    for variant in variants:
        other = encode_places(layout, readings, {("appearance", "light"): variant})
        assert other.bundle is not None
        assert first.reference_set_fingerprint != other.reference_set_fingerprint
        assert first.bundle.layout != other.bundle.layout
        assert (
            add_counts(first.bundle, other.bundle).code is CountCode.IDENTITY_MISMATCH
        )
        assert other.reference_set_fingerprint is not None
        assert (
            decode_count_names(layout, first.bundle, other.reference_set_fingerprint)
            is None
        )


def test_uint64_digit_edges_compare_without_float_rounding() -> None:
    _, layout = fixture_layout()
    edge = float(1 << 53)
    values = np.array([1 << 53, (1 << 53) + 1], dtype=np.uint64)
    result = encode_places(
        layout,
        {
            ("appearance", "light"): reading("appearance", "light", values),
            ("context", "route"): reading("context", "route", ["first", "last"]),
        },
        {("appearance", "light"): reference(layout, low=edge, high=edge)},
    )
    assert result.bundle is not None
    assert result.metrics[0].row_codes.tolist() == [1, 2]


def _scalar_digit_reference(values, available, low, high, row_start):
    expected = np.full(values.shape, -1, dtype=np.int16)
    for index in np.ndindex(values.shape):
        value = values[index].item()
        if not available[index] or not np.isfinite(value):
            continue
        if value < low:
            expected[index] = row_start
        elif value > high:
            expected[index] = row_start + 2
        else:
            expected[index] = row_start + 1
    return expected


def test_safe_vector_digit_paths_match_scalar_reference() -> None:
    cases = (
        (np.array([0, 1, 2, 3, 4, 65535], dtype=np.uint16), 1, 3),
        (
            np.array([-1.0, -0.25, 0.0, 0.25, 1.0, np.nan], dtype=np.float32),
            -0.25,
            0.25,
        ),
        (
            np.array([-2.0, -0.5, 0.5, 2.0, np.inf], dtype=np.float64),
            -0.5,
            0.5,
        ),
    )
    for values, low, high in cases:
        available = np.array([True, True, False, True, True, True][: values.size])
        assert _can_vectorize_digit_compare(values, low, high)
        actual, _ = _digit_row_codes(values, available, low, high, 7)
        expected = _scalar_digit_reference(values, available, low, high, 7)
        np.testing.assert_array_equal(actual, expected)


def test_wide_integer_digit_path_uses_exact_scalar_fallback() -> None:
    edge = float(1 << 53)
    values = np.array([1 << 53, (1 << 53) + 1], dtype=np.uint64)
    available = np.ones(values.shape, dtype=np.bool_)
    assert not _can_vectorize_digit_compare(values, edge, edge)
    actual, _ = _digit_row_codes(values, available, edge, edge, 0)
    expected = _scalar_digit_reference(values, available, edge, edge, 0)
    np.testing.assert_array_equal(actual, expected)
    assert actual.tolist() == [1, 2]


def test_unused_carrier_rows_must_remain_zero_when_decoding() -> None:
    _, layout = fixture_layout()
    result = encode_places(
        layout,
        {
            ("appearance", "light"): reading("appearance", "light", [0.0]),
            ("context", "route"): reading("context", "route", ["first"]),
        },
        {("appearance", "light"): reference(layout)},
    )
    assert result.bundle is not None and result.reference_set_fingerprint is not None
    counts = [list(bank) for bank in result.bundle.counts]
    counts[0][511] = 1
    malformed = replace(result.bundle, counts=tuple(tuple(bank) for bank in counts))
    assert (
        decode_count_names(layout, malformed, result.reference_set_fingerprint) is None
    )
    wrong_length = replace(
        result.bundle, counts=(result.bundle.counts[0][:-1], result.bundle.counts[1])
    )
    assert (
        decode_count_names(layout, wrong_length, result.reference_set_fingerprint)
        is None
    )
    negative_counts = [list(bank) for bank in result.bundle.counts]
    negative_counts[0][0] = -1
    negative = replace(
        result.bundle, counts=tuple(tuple(bank) for bank in negative_counts)
    )
    assert (
        decode_count_names(layout, negative, result.reference_set_fingerprint) is None
    )


def test_multiple_metrics_have_disjoint_sequential_rows_with_vectorized_counts() -> (
    None
):
    layout = compile_layout(
        LayoutSpec(
            "single-bank-v1",
            "carrier-test-v1",
            (
                BankSpec(
                    "bank",
                    "facet",
                    (
                        MetricSpec("digit", MetricKind.DIGIT),
                        MetricSpec("word", MetricKind.WORDS, ("a", "b")),
                    ),
                ),
            ),
        )
    )
    assert layout is not None
    digit_ref = NumericReference(
        layout.fingerprint, "bank", "digit", "ref", "source", "unit", 0, 0
    )
    result = encode_places(
        layout,
        {
            ("bank", "digit"): reading("bank", "digit", [-1, 0, 1]),
            ("bank", "word"): reading("bank", "word", ["b", "a", "b"]),
        },
        {("bank", "digit"): digit_ref},
    )
    assert result.bundle is not None
    assert result.bundle.counts[0][:5] == (1, 1, 1, 1, 2)
    assert not any(result.bundle.counts[0][5:])
    assert result.metrics[0].row_codes.tolist() == [0, 1, 2]
    assert result.metrics[1].row_codes.tolist() == [4, 3, 4]


def test_nonfinite_values_are_not_written_and_empty_places_are_silent() -> None:
    _, layout = fixture_layout()
    values = np.array([np.nan, np.inf, 0.0])
    result = encode_places(
        layout,
        {
            ("appearance", "light"): reading("appearance", "light", values),
            ("context", "route"): reading(
                "context", "route", ["first", "last", "search"]
            ),
        },
        {("appearance", "light"): reference(layout)},
    )
    assert result.bundle is not None
    assert result.metrics[0].row_codes.tolist() == [-1, -1, 1]
    assert result.metrics[0].nonfinite_available_count == 2
    empty = encode_places(
        layout,
        {
            ("appearance", "light"): reading(
                "appearance", "light", np.array([], dtype=float)
            ),
            ("context", "route"): reading("context", "route", np.array([], dtype=str)),
        },
        {("appearance", "light"): reference(layout)},
    )
    assert empty.status is EncodingCode.SILENT
    assert empty.bundle is not None


def test_count_bundle_is_independent_of_reading_mapping_order() -> None:
    _, layout = fixture_layout()
    digit = reading("appearance", "light", [-1.0, 0.0, 1.0])
    words = reading("context", "route", ["first", "last", "first"])
    ref = reference(layout)
    forward = encode_places(
        layout,
        {("appearance", "light"): digit, ("context", "route"): words},
        {("appearance", "light"): ref},
    )
    reverse = encode_places(
        layout,
        {("context", "route"): words, ("appearance", "light"): digit},
        {("appearance", "light"): ref},
    )
    assert forward.bundle is not None and reverse.bundle is not None
    assert forward.bundle == reverse.bundle
    assert add_counts(forward.bundle, reverse.bundle).code is CountCode.OK


def test_layout_fingerprint_tracks_order_and_allows_more_than_sixteen_banks() -> None:
    _, original = fixture_layout()
    reordered = compile_layout(
        LayoutSpec(
            "schema-v1",
            "carrier-test-v1",
            (
                BankSpec(
                    "context",
                    "facet-b",
                    (
                        MetricSpec(
                            "route", MetricKind.WORDS, ("first", "search", "last")
                        ),
                    ),
                ),
                BankSpec(
                    "appearance", "facet-a", (MetricSpec("light", MetricKind.DIGIT),)
                ),
            ),
        )
    )
    assert reordered is not None
    assert reordered.fingerprint != original.fingerprint
    many = compile_layout(
        LayoutSpec(
            "many-v1",
            "carrier-test-v1",
            tuple(
                BankSpec(
                    f"bank-{index}", "facet", (MetricSpec("value", MetricKind.DIGIT),)
                )
                for index in range(17)
            ),
        )
    )
    assert many is not None
    assert len(many.count_layout.banks) == 17


def test_bank_row_capacity_is_enforced_at_512() -> None:
    accepted = compile_layout(
        LayoutSpec(
            "rows-v1",
            "carrier-test-v1",
            (
                BankSpec(
                    "wide",
                    "facet",
                    (
                        MetricSpec(
                            "words",
                            MetricKind.WORDS,
                            tuple(f"w{i}" for i in range(512)),
                        ),
                    ),
                ),
            ),
        )
    )
    rejected = compile_layout(
        LayoutSpec(
            "rows-v1",
            "carrier-test-v1",
            (
                BankSpec(
                    "wide",
                    "facet",
                    (
                        MetricSpec(
                            "words",
                            MetricKind.WORDS,
                            tuple(f"w{i}" for i in range(510)),
                        ),
                        MetricSpec("digit", MetricKind.DIGIT),
                    ),
                ),
            ),
        )
    )
    assert accepted is not None
    assert accepted.count_layout.banks[0].row_count == 512
    assert rejected is None


def test_nonfinite_or_reversed_reference_is_invalid() -> None:
    _, layout = fixture_layout()
    values = reading("appearance", "light", [0.0])
    words = reading("context", "route", ["first"])
    for bad_reference in (
        replace(reference(layout), low=float("nan")),
        replace(reference(layout), low=2.0, high=1.0),
    ):
        result = encode_places(
            layout,
            {("appearance", "light"): values, ("context", "route"): words},
            {("appearance", "light"): bad_reference},
        )
        assert result.status is EncodingCode.INVALID_INPUT
        assert result.bundle is None


def test_invalid_shapes_and_boolean_numeric_values_are_rejected() -> None:
    _, layout = fixture_layout()
    wrong_mask = PlaceReading(
        "appearance", "light", np.array([0.0, 1.0]), np.array([True])
    )
    result = encode_places(
        layout,
        {
            ("appearance", "light"): wrong_mask,
            ("context", "route"): reading("context", "route", ["first", "first"]),
        },
        {("appearance", "light"): reference(layout)},
    )
    assert result.status is EncodingCode.INVALID_INPUT
    bool_values = PlaceReading(
        "appearance", "light", np.array([True]), np.array([True], dtype=np.bool_)
    )
    result = encode_places(
        layout,
        {
            ("appearance", "light"): bool_values,
            ("context", "route"): reading("context", "route", ["first"]),
        },
        {("appearance", "light"): reference(layout)},
    )
    assert result.status is EncodingCode.INVALID_INPUT


def test_unread_numeric_facet_needs_no_reference_and_writes_no_middle_row():
    _, layout = fixture_layout()
    result = encode_places(
        layout,
        {
            ("appearance", "light"): reading(
                "appearance", "light", [0.0, 0.0], [False, False]
            ),
            ("context", "route"): reading("context", "route", ["first", "last"]),
        },
        {},
    )
    assert result.status is EncodingCode.OK
    assert result.metrics[0].status is EncodingCode.SILENT
    assert result.metrics[0].row_codes.tolist() == [-1, -1]
    assert result.bundle is not None
    assert not any(result.bundle.counts[0])
    assert sum(result.bundle.counts[1]) == 2
