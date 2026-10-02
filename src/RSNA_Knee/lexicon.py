"""Domain Lexicon — Scale 0 vocabulary mapping.

Pattern 11: External Ontologies/Databases as Parsers. Don't hand-curate
vocabulary — use existing domain databases as zero-cost parsers.

Each term maps to a bank assignment with a confidence score.
Lookup is O(1) by name/synonym.

Reference: DATA_GEOMETRY_ARCHITECTURE.md, Pattern 11.
"""

from __future__ import annotations

# TODO: Define domain-specific vocabulary maps.
# Example structure from NCEMS:
#   INSTRUMENT_MAP = {
#       "q exactive": "AC=MS:1001911;NT=Q Exactive",
#       ...
#   }
#
# Example structure from swiss_legal:
#   ENGLISH_TO_GERMAN = {
#       "pre-trial detention": ["Untersuchungshaft", "Sicherheitshaft"],
#       ...
#   }


def normalize_value(value: str) -> str:
    """Normalize a raw extracted value to canonical form.

    TODO: Implement domain-specific normalization.
    """
    return value.strip()
