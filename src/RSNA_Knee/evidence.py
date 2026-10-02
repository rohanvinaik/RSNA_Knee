"""Shadow Ledger / Evidence Container — Pattern 5.

Store ALL extracted evidence with provenance, scope, and confidence.
The shadow ledger is intentionally richer than the final output.
Extraction maximizes recall; emission (Pattern 8) maximizes precision.

Evidence scope classification:
- SAMPLE/DIRECT: directly relevant to the output
- BACKGROUND: mentioned as context, not about this instance
- METHOD_ONLY: appears in supporting material without clear binding

Each evidence record stores: value, normalized value, target field,
source (which pipeline stage found it), confidence, scope, context snippet.

Reference: DATA_GEOMETRY_ARCHITECTURE.md, Pattern 5.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum, IntEnum


class EvidenceScope(Enum):
    """How a mention relates to the actual output."""

    DIRECT = "direct"
    BACKGROUND = "background"
    METHOD_ONLY = "method_only"


class BankId(IntEnum):
    """Orthogonal evaluation dimensions. TODO: Define domain-specific banks.

    Each bank evaluates candidates independently. The interference pattern
    across banks determines the final decision (Pattern 6).
    """

    BANK_0 = 0
    BANK_1 = 1
    BANK_2 = 2
    BANK_3 = 3


def to_ternary(value: float, threshold: float) -> int:
    """Convert continuous score to OTP ternary {-1, 0, +1}.

    0 = orthogonal (informational zero, NOT absence).
    +1 = supports. -1 = opposes.
    """
    if value > threshold:
        return 1
    if value < -threshold:
        return -1
    return 0


@dataclass
class CandidateSignals:
    """All bank signals for a single candidate.

    Following Yami's MoveSignals pattern: every candidate gets
    ALL signals evaluated independently.
    """

    candidate_id: str
    bank_scores: dict[BankId, float] = field(default_factory=dict)
    bank_ternary: dict[BankId, int] = field(default_factory=dict)
    supports: int = 0
    opposes: int = 0
    interference: float = 0.0
    final_score: float = 0.0
    discovery_sources: set[str] = field(default_factory=set)
    scope: EvidenceScope = EvidenceScope.DIRECT

    def compute_interference(self) -> None:
        """Compute OTP interference pattern across banks.

        TODO: Calibrate thresholds and COEC bonuses from training data.
        """
        tv = list(self.bank_ternary.values())
        self.supports = sum(1 for t in tv if t == 1)
        self.opposes = sum(1 for t in tv if t == -1)

        if self.supports >= 3:
            self.interference = self.supports * 1.5
        elif self.opposes >= 2:
            self.interference = -self.opposes * 1.0
        else:
            self.interference = (self.supports - self.opposes) * 0.5

        # TODO: Add COEC compositional amplification for domain-specific
        # bank pairs. See DATA_GEOMETRY_ARCHITECTURE.md, Pattern 6.

        self.final_score = sum(self.bank_scores.values()) + self.interference


@dataclass
class EvidenceLedger:
    """Tracks all candidates with their bank evaluations."""

    _entries: dict[str, CandidateSignals] = field(default_factory=dict)

    def add_candidate(self, candidate_id: str, source: str) -> CandidateSignals:
        if candidate_id not in self._entries:
            self._entries[candidate_id] = CandidateSignals(candidate_id=candidate_id)
        self._entries[candidate_id].discovery_sources.add(source)
        return self._entries[candidate_id]

    def get_ranked(self) -> list[CandidateSignals]:
        return sorted(self._entries.values(), key=lambda e: e.final_score, reverse=True)

    @property
    def all_entries(self) -> list[CandidateSignals]:
        return list(self._entries.values())

    def __len__(self) -> int:
        return len(self._entries)
