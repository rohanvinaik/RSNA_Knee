"""KneeDiff — the per-cell statistical residual (THEORY II.3).

The dense continuous generalization of GenomeVault's GDiff: the analysis
pixel's deviation from the reference cell's DISTRIBUTION, normalized by that
cell's spread. The cell's spread IS its tolerance (THEORY II.2) — where the
reference knees genuinely vary, sigma is wide and normal variation zeros out;
only deviation the reference does not license survives the threshold.

NOT ported: `differential_encoding/differences.py` (sparse set-difference over
discrete keys — wrong semantics for dense pixels; see THEORY II.3 precision
note). After the dense subtract, thresholding makes the residual sparse again.

Layering (house rules): every DECISION here is a pure, total function over
scalars/lists, Detective-pinnable; the numpy array shell lives in
`platonic_reference.py` and only vectorizes these same definitions.
"""

from __future__ import annotations


def residual_z(value: float, mu: float, sigma: float, sigma_floor: float) -> float:
    """Per-cell statistical residual: deviation in units of the cell's spread.

    `sigma_floor` guards zero-variance cells (masked background, perfectly
    agreeing anatomy) from dividing by ~0 and must be > 0. The floor is a
    tolerance, not a fudge: a cell whose references agree perfectly still
    tolerates measurement noise of about `sigma_floor`.
    """
    spread = max(sigma_floor, sigma)
    return (value - mu) / spread


def classify_cell(z: float, z_thresh: float) -> str:
    """Classify one cell's residual against the reference's license.

    Returns named codes (never bools — "within" and "deviant" must not
    collapse into a truthy check):
      "within_tolerance" — the reference licenses this value; it zeros out
      "deviant"          — deviation the reference does not license; survives
    """
    if z >= z_thresh or z <= -z_thresh:
        return "deviant"
    return "within_tolerance"


def survival_fraction(zs: list, z_thresh: float) -> float:
    """Fraction of cells whose residual survives the threshold.

    The S/N collapse in one number: on a held-out NORMAL study this should be
    small (the reference absorbed it); on an ABNORMAL study, larger.
    Empty input returns 0.0 (nothing survives from nothing).
    """
    if not zs:
        return 0.0
    deviant = sum(1 for z in zs if classify_cell(z, z_thresh) == "deviant")
    return deviant / len(zs)


def window_is_scorable(knee_count: int, window_cells: int, min_knee_frac: float) -> str:
    """Decide whether a window contains enough knee tissue to score.

    A window mostly outside the knee mask must not contribute a density —
    off-knee cells are excluded from the statistic entirely (II.1's mask),
    and a window of 3 knee cells where all 3 deviate is not a 100%-dense
    lesion candidate. Named codes:
      "scorable"          — knee coverage meets the bar; density is meaningful
      "insufficient_knee" — too little tissue in view; window is skipped
    """
    if knee_count >= min_knee_frac * window_cells:
        return "scorable"
    return "insufficient_knee"


def make_or_break_verdict(
    auc: float,
    n_normal: int,
    n_abnormal: int,
    min_studies: int,
    absorb_bar: float = 0.90,
    signal_bar: float = 0.65,
) -> str:
    """THE make-or-break decision (THEORY Part III closing note).

    Does the entropy-weighted reference absorb normal anatomical variation and
    leave only pathology in the residual? Measured the way the competition
    itself measures: the ROC-AUC of a residual statistic (peak local survivor
    density) ranking abnormal studies above held-out normal ones. Rank-based,
    so no absolute threshold or margin knob to hand-tune — an early
    fraction+margin variant of this verdict was calibration-fragile by
    construction (small-N sigma noise + smooth-field clustering shift absolute
    levels; they shift ranks far less).

    The bars are PROVISIONAL until calibrated on real data (Pattern 19).

    Returns named codes:
      "insufficient_data" — fewer than `min_studies` per side; the question is
                            OPEN, not answered (never conflate cannot-determine
                            with determined-false)
      "reference_absorbs" — auc >= absorb_bar: the residual statistic cleanly
                            ranks pathology above licensed variation
      "partial_signal"    — signal_bar <= auc < absorb_bar: signal present,
                            separation not clean; iterate the encoder (Law 5)
      "no_separation"     — auc < signal_bar: the residual is not carrying the
                            pathology signal
    """
    if n_normal < min_studies or n_abnormal < min_studies:
        return "insufficient_data"
    if auc >= absorb_bar:
        return "reference_absorbs"
    if auc >= signal_bar:
        return "partial_signal"
    return "no_separation"
