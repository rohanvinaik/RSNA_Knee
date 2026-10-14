"""Intent tests for the collapse's pure decisions (knee.collapse.codes), written from the contract:
one noise law per series read two independent ways, concurrence is the measurement that the law
holds, disagreement is a finding and never a refit, every zero says which zero it is, and every bar
a decision reads is an argument and never a constant inside it."""

from knee.collapse.codes import (
    coil_code,
    concurrence_code,
    normalization_code,
    quiet_code,
    storage_code,
)


def test_a_quiet_population_with_spread_is_readable() -> None:
    assert quiet_code(n_finite=500, n_zero=0, spread=3.2, min_count=100) == "readable"


def test_each_kind_of_zero_in_the_quiet_population_is_its_own_code() -> None:
    assert quiet_code(n_finite=0, n_zero=0, spread=0.0, min_count=100) == "no_values"
    assert quiet_code(n_finite=20, n_zero=0, spread=3.2, min_count=100) == "too_few"
    assert (
        quiet_code(n_finite=500, n_zero=500, spread=0.0, min_count=100)
        == "background_masked"
    )
    assert quiet_code(n_finite=500, n_zero=10, spread=0.0, min_count=100) == "no_spread"


def test_a_masked_background_is_not_a_dark_reading() -> None:
    # 62 of this corpus's 336 series are over 20% zeros. Where every quiet value is exactly zero the
    # vendor masked the background: that is not a sigma of zero, it is no reading at all.
    assert (
        quiet_code(n_finite=800, n_zero=800, spread=0.0, min_count=10)
        == "background_masked"
    )


def test_a_spread_that_is_not_a_number_is_no_spread() -> None:
    assert (
        quiet_code(n_finite=500, n_zero=0, spread=float("nan"), min_count=10)
        == "no_spread"
    )
    assert quiet_code(n_finite=500, n_zero=0, spread=-1.0, min_count=10) == "no_spread"


def test_the_min_count_is_the_callers_bar_not_the_decisions() -> None:
    assert quiet_code(n_finite=50, n_zero=0, spread=1.0, min_count=100) == "too_few"
    assert quiet_code(n_finite=50, n_zero=0, spread=1.0, min_count=10) == "readable"


def test_one_channel_reads_a_moment_ratio_of_exactly_two() -> None:
    # (L + 1) / L at L = 1.
    assert coil_code(2.0, single_tolerance=0.1) == "single"


def test_more_channels_drive_the_ratio_toward_one() -> None:
    assert coil_code(1.5, single_tolerance=0.1) == "multi"  # L = 2
    assert coil_code(1.25, single_tolerance=0.1) == "multi"  # L = 4


def test_a_ratio_the_identity_cannot_hold_is_named_not_coerced() -> None:
    for ratio in (1.0, 0.5, 0.0, -1.0, 2.5, 10.0):
        assert coil_code(ratio, single_tolerance=0.1) == "implausible_ratio", ratio


def test_a_ratio_that_is_not_a_number_is_unmeasurable() -> None:
    assert coil_code(float("nan"), single_tolerance=0.1) == "unmeasurable"
    assert coil_code(float("inf"), single_tolerance=0.1) == "unmeasurable"


def test_two_estimators_within_sampling_error_concur() -> None:
    # Standard error of a spread from n samples is sigma / sqrt(2n): at n = 5000 and sigma = 10 that
    # is 0.1 each, so a gap of 0.05 is well inside two of them.
    assert concurrence_code(10.0, 10.05, 5000, 5000, tolerance_errors=2.0) == "concur"


def test_two_estimators_far_apart_disagree_and_are_not_refitted() -> None:
    assert concurrence_code(10.0, 40.0, 5000, 5000, tolerance_errors=2.0) == "disagree"


def test_an_abstention_is_kept_apart_from_a_disagreement() -> None:
    assert (
        concurrence_code(float("nan"), 10.0, 0, 5000, tolerance_errors=2.0)
        == "dark_abstained"
    )
    assert (
        concurrence_code(10.0, float("nan"), 5000, 0, tolerance_errors=2.0)
        == "bright_abstained"
    )
    assert (
        concurrence_code(float("nan"), float("nan"), 0, 0, tolerance_errors=2.0)
        == "both_abstained"
    )


def test_a_sigma_of_zero_is_an_abstention_never_a_reading() -> None:
    # A masked background drives the dark estimator to zero. Zero is not a narrow sigma.
    assert (
        concurrence_code(0.0, 10.0, 5000, 5000, tolerance_errors=2.0)
        == "dark_abstained"
    )


def test_the_tolerance_is_the_callers_bar() -> None:
    assert concurrence_code(10.0, 10.5, 5000, 5000, tolerance_errors=1.0) == "disagree"
    assert concurrence_code(10.0, 10.5, 5000, 5000, tolerance_errors=20.0) == "concur"


def test_a_wider_sample_narrows_what_counts_as_concurrence() -> None:
    # The same gap concurs on few samples and disagrees on many: the error shrinks as 1/sqrt(n).
    assert concurrence_code(10.0, 10.6, 50, 50, tolerance_errors=2.0) == "concur"
    assert (
        concurrence_code(10.0, 10.6, 500000, 500000, tolerance_errors=2.0) == "disagree"
    )


def test_what_is_declared_and_what_is_held_are_two_readings() -> None:
    assert storage_code(0, 0) == "unsigned"
    assert storage_code(1, 0) == "signed_nonnegative"
    assert storage_code(1, 7) == "signed_negative"


def test_a_file_contradicting_itself_is_carried_not_coerced() -> None:
    assert storage_code(0, 3) == "unsigned_negative"


def test_an_unknown_representation_is_named() -> None:
    assert storage_code(2, 0) == "unknown_representation"
    assert storage_code(-1, 0) == "unknown_representation"


def test_the_vendors_normalization_flag_is_read_from_the_header() -> None:
    assert normalization_code(("ORIGINAL", "PRIMARY", "M", "NORM")) == "normalized"


def test_a_header_that_does_not_say_is_not_a_header_that_denies() -> None:
    assert normalization_code(("ORIGINAL", "PRIMARY", "M_SE", "M")) == "not_flagged"
    assert normalization_code(()) == "unknown"
