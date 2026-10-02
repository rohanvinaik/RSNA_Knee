"""Phase D Healing — Pattern 18.

After the main pipeline produces output, a second pass promotes
low-confidence candidates that meet structural criteria.

Healing is a constraint-satisfier, not a generator. It picks from
the existing candidate set based on structural signals.

Reference: DATA_GEOMETRY_ARCHITECTURE.md, Pattern 18.
"""

from __future__ import annotations

from .evidence import EvidenceLedger


def heal_candidates(
    ledger: EvidenceLedger,
    predicted: list[str],
    max_heals: int = 10,
    min_criteria: int = 2,
) -> list[str]:
    """Promote low-confidence candidates into the predicted set.

    TODO: Define domain-specific healing criteria.
    Each candidate below the cutoff must meet min_criteria of:
    - Graph-connected to seeds
    - Found by multiple discovery sources
    - Correct domain/authority match
    - Structural position consistent with query pattern
    """
    predicted_set = set(predicted)
    healed = []

    for entry in ledger.get_ranked():
        if len(healed) >= max_heals:
            break
        if entry.candidate_id in predicted_set:
            continue

        criteria_met = 0
        # TODO: Implement domain-specific criteria checks
        # if entry.bank_ternary.get(BankId.PRECEDENT) == 1:
        #     criteria_met += 1
        # if len(entry.discovery_sources) >= 2:
        #     criteria_met += 1

        if criteria_met >= min_criteria:
            healed.append(entry.candidate_id)

    return predicted + healed
