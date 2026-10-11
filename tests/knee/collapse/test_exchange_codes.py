"""Named outcomes for transporting native dark-run evidence."""

import pytest
from hypothesis import given
from hypothesis import strategies as st

from knee.collapse.exchange_codes import exchange_code


@pytest.mark.parametrize(
    ("coverage", "valid", "samples", "runs", "bounded", "open", "expected"),
    [
        ("covered", 0, 0, 0, 0, 0, "empty_profile"),
        ("covered", 2, 3, 0, 0, 0, "native_missing"),
        ("covered", 3, 3, 1, 0, 1, "native_open"),
        ("covered", 5, 5, 3, 2, 1, "native_open"),
        ("covered", 5, 5, 3, 2, 0, "native_multiple"),
        ("covered", 5, 5, 3, 1, 0, "concurrent"),
        ("covered", 3, 3, 0, 0, 0, "peer_only"),
        ("covered", 3, 3, 1, 0, 0, "disagreement"),
        ("outside_slab", 0, 0, 0, 0, 0, "outside_slab"),
        (
            "slab_support_unknown",
            0,
            0,
            0,
            0,
            0,
            "slab_support_unknown",
        ),
        ("normal_unavailable", 0, 0, 0, 0, 0, "normal_unavailable"),
    ],
)
def test_exchange_codes_preserve_distinct_readings(
    coverage, valid, samples, runs, bounded, open, expected
) -> None:
    assert exchange_code(coverage, valid, samples, runs, bounded, open) == expected


@pytest.mark.parametrize(
    ("coverage", "valid", "samples", "runs", "bounded", "open"),
    [
        ("unknown", 0, 0, 0, 0, 0),
        ("covered", -1, 1, 0, 0, 0),
        ("covered", 2, 1, 0, 0, 0),
        ("covered", 0, -1, 0, 0, 0),
        ("covered", 0, 1, -1, 0, 0),
        ("covered", 0, 2, 2, 0, 0),
        ("covered", 0, 1, 1, -1, 0),
        ("covered", 0, 1, 1, 0, -1),
        ("covered", 0, 1, 1, 1, 1),
    ],
)
def test_invalid_counts_and_coverage_have_a_named_refusal(
    coverage, valid, samples, runs, bounded, open
) -> None:
    assert (
        exchange_code(coverage, valid, samples, runs, bounded, open)
        == "invalid_measurement"
    )


@pytest.mark.parametrize(
    ("valid", "samples", "runs", "bounded", "open"),
    [
        (-1, 0, 0, 0, 0),
        (1, 0, 0, 0, 0),
        (0, -1, 0, 0, 0),
        (0, 0, -1, 0, 0),
        (0, 1, 1, -1, 0),
        (0, 1, 1, 0, -1),
        (0, 1, 1, 1, 1),
    ],
)
def test_invalid_measurement_precedes_unavailable_coverage(
    valid, samples, runs, bounded, open
) -> None:
    assert (
        exchange_code("outside_slab", valid, samples, runs, bounded, open)
        == "invalid_measurement"
    )


@given(
    samples=st.integers(min_value=1, max_value=1000),
)
def test_valid_run_count_boundary_is_ceiling_half_of_samples(
    samples: int,
) -> None:
    max_runs = (samples + 1) // 2
    assert exchange_code("covered", samples, samples, max_runs, 1, 0) == "concurrent"
    assert (
        exchange_code("covered", samples, samples, max_runs + 1, 1, 0)
        == "invalid_measurement"
    )


@given(
    samples=st.integers(min_value=1, max_value=1000),
    valid=st.integers(min_value=0, max_value=1000),
)
def test_valid_sample_count_boundary(samples: int, valid: int) -> None:
    valid = min(valid, samples)
    assert exchange_code("covered", valid, samples, 0, 0, 0) == (
        "native_missing" if valid < samples else "peer_only"
    )


def test_alternating_run_count_above_float_integer_precision() -> None:
    # An alternating sequence beginning and ending dark has one more dark run
    # than bright separators. Count reasoning must remain exact without arrays.
    samples = 18_014_398_509_481_985
    dark_runs = 9_007_199_254_740_993
    assert exchange_code("covered", samples, samples, dark_runs, 1, 0) == "concurrent"
    assert (
        exchange_code("covered", samples, samples, dark_runs + 1, 1, 0)
        == "invalid_measurement"
    )
