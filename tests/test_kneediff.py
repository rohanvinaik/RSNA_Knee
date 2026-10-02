"""Intent tests for the KneeDiff pure decision core (THEORY II.2-II.3).

Authored from the MECHANISM: spread is tolerance, deviation the reference
does not license survives, the verdict speaks in named codes and never
conflates cannot-determine with determined-false.
"""

from RSNA_Knee.kneediff import (
    classify_cell,
    make_or_break_verdict,
    residual_z,
    survival_fraction,
)

# --- residual_z: spread IS the tolerance -------------------------------------


def test_residual_uses_cell_spread():
    assert residual_z(1.0, 0.0, 0.5, 0.05) == 2.0


def test_residual_wide_cell_absorbs_more():
    # same deviation, wider cell -> smaller residual: normal variation zeroing out
    narrow = residual_z(1.0, 0.0, 0.2, 0.05)
    wide = residual_z(1.0, 0.0, 1.0, 0.05)
    assert abs(wide) < abs(narrow)


def test_residual_floor_guards_zero_variance_cells():
    # perfectly agreeing references still tolerate ~sigma_floor of noise
    assert residual_z(0.1, 0.0, 0.0, 0.05) == 2.0


def test_residual_sign_preserved():
    assert residual_z(-1.0, 0.0, 0.5, 0.05) == -2.0


# --- classify_cell: named codes, symmetric threshold -------------------------


def test_within_tolerance_zeroes_out():
    assert classify_cell(2.9, 3.0) == "within_tolerance"


def test_deviant_survives_both_signs():
    assert classify_cell(3.0, 3.0) == "deviant"
    assert classify_cell(-3.0, 3.0) == "deviant"


# --- survival_fraction --------------------------------------------------------


def test_survival_fraction_counts_deviants():
    assert survival_fraction([0.0, 1.0, 3.5, -4.0], 3.0) == 0.5


def test_survival_fraction_empty_is_zero():
    assert survival_fraction([], 3.0) == 0.0


# --- make_or_break_verdict: the named codes ----------------------------------


def test_insufficient_data_never_becomes_a_no():
    # cannot-determine must not collapse into determined-false
    assert make_or_break_verdict(0.99, 2, 8, 3) == "insufficient_data"
    assert make_or_break_verdict(0.99, 8, 2, 3) == "insufficient_data"


def test_clean_separation_is_reference_absorbs():
    assert make_or_break_verdict(0.95, 8, 8, 3) == "reference_absorbs"
    assert make_or_break_verdict(0.90, 8, 8, 3) == "reference_absorbs"


def test_partial_signal_band():
    assert make_or_break_verdict(0.75, 8, 8, 3) == "partial_signal"
    assert make_or_break_verdict(0.65, 8, 8, 3) == "partial_signal"


def test_no_separation_below_signal_bar():
    assert make_or_break_verdict(0.64, 8, 8, 3) == "no_separation"
    assert make_or_break_verdict(0.5, 8, 8, 3) == "no_separation"
