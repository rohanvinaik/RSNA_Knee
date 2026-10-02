"""Pipeline Orchestrator — Pattern 3: Multi-Scale Lens Architecture.

Orchestrates all scales in order. Each scale resolves uncertainties
left by the scale below it. Higher scales only fire when lower
scales have ambiguity (GSE residual principle).

Scale hierarchy:
  Scale -1: Domain classification (Pattern 2) — constrains search space
  Scale 0:  Lexicon/ontology scan (Pattern 11) — deterministic mapping
  Scale 1:  Context disambiguation — which bank does this term belong to?
  Scale 2:  Cross-validation — do multiple sources agree?
  Scale 3:  Bank evaluation (Pattern 6) — OTP interference detection
  Scale 3.5: Coherence inference (Pattern 7) — trajectory disambiguation
  Scale 3.75: Symbolic healing (Pattern 10) — constraint propagation
  Scale 4:  Neural residual (Pattern 13) — LLM for irreducible ambiguity

Reference: DATA_GEOMETRY_ARCHITECTURE.md, Pattern 3.
"""

from __future__ import annotations

from dataclasses import dataclass

from .bank_evaluator import evaluate_all_banks
from .domain_classifier import classify
from .evidence import EvidenceLedger
from .healing import heal_candidates


@dataclass
class PipelineConfig:
    """Configuration for the pipeline. Calibrate from training (Pattern 19)."""

    max_output: int = 40
    min_output: int = 5


class Pipeline:
    """Multi-scale pipeline with OTP bank evaluation."""

    def __init__(self, config: PipelineConfig | None = None):
        self.config = config or PipelineConfig()
        # TODO: Load domain-specific assets (corpus, graph, index, etc.)

    def process(self, input_data) -> tuple[list, EvidenceLedger]:
        """Run full pipeline: discovery → evaluation → healing."""
        ledger = EvidenceLedger()

        # Scale -1: Domain classification
        classification = classify(str(input_data))

        # Scale 0: Lexicon/ontology scan
        # TODO: deterministic term matching

        # Scale 1-2: Context disambiguation + cross-validation
        # TODO: context windows, cross-section validation

        # Scale 3: Bank evaluation
        evaluate_all_banks(ledger, classification=classification)

        # Scale 3.5: Trajectory disambiguation for ambiguous candidates
        # TODO: apply trajectory scoring to entries with 2-3 supports

        # Collect ranked results
        predicted = [
            e.candidate_id for e in ledger.get_ranked()[: self.config.max_output]
        ]

        # Scale 3.75 / Phase D: Healing
        predicted = heal_candidates(ledger, predicted)

        return predicted, ledger


if __name__ == "__main__":
    print("Pipeline not yet configured. Follow the Adaptation Checklist in README.md.")
