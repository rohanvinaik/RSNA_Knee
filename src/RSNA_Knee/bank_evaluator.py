"""Bank Evaluator — Pattern 6: OTP Bank Evaluation with Interference.

Score every candidate on ALL banks independently. The interference pattern
across banks determines the final decision.

Banks score from STRUCTURAL POSITION, not text. Language-agnostic by construction.

Implementation:
1. Define per-bank scoring functions
2. Convert continuous scores to ternary {-1, 0, +1}
3. Compute interference pattern
4. Apply COEC compositional amplification for co-supporting bank pairs

Thresholds and weights MUST be calibrated from training data (Pattern 19).

Reference: DATA_GEOMETRY_ARCHITECTURE.md, Pattern 6.
"""

from __future__ import annotations

from .evidence import BankId, EvidenceLedger

# Per-bank ternary conversion thresholds. TODO: Calibrate from training.
THRESHOLDS: dict[BankId, float] = {
    BankId.BANK_0: 0.3,
    BankId.BANK_1: 0.2,
    BankId.BANK_2: 0.2,
    BankId.BANK_3: 0.2,
}


def evaluate_all_banks(ledger: EvidenceLedger, **kwargs) -> None:
    """Evaluate ALL bank signals for EVERY candidate.

    TODO: Implement domain-specific bank scoring functions.
    Each bank computes from structural position — anchor overlap,
    graph distance, hierarchy depth, domain alignment.
    """
    for entry in ledger.all_entries:
        # TODO: Score each bank
        # entry.bank_scores[BankId.BANK_0] = _score_bank_0(entry, **kwargs)
        # entry.bank_ternary[BankId.BANK_0] = to_ternary(
        #     entry.bank_scores[BankId.BANK_0], THRESHOLDS[BankId.BANK_0]
        # )
        pass

    # Compute interference for all entries
    for entry in ledger.all_entries:
        entry.compute_interference()
