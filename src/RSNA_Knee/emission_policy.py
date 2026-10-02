"""Emission Policy — Pattern 8: Schema-Family-Specific Rules.

Not all evidence should be emitted. The emission policy defines
per-schema-family rules for what crosses the shadow→output boundary.

Policy dimensions:
- suppress: never emit for this family
- require_source: evidence must come from authoritative sources
- expected: these fields should be filled; absence triggers healing
- confidence_threshold: minimum confidence before emission

Reference: DATA_GEOMETRY_ARCHITECTURE.md, Pattern 8.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class EmissionPolicy:
    """Allowed output behavior for one schema family."""

    family: str
    suppress_fields: frozenset[str] = field(default_factory=frozenset)
    expected_fields: frozenset[str] = field(default_factory=frozenset)
    confidence_thresholds: dict[str, float] = field(default_factory=dict)


# TODO: Define per-schema-family policies.
# Example from NCEMS (10 families):
#   "synthetic": suppress Disease, CellLine, Sex
#   "tissue": expect OrganismPart, Disease, MaterialType
#
# Example from swiss_legal:
#   wrong-domain statutes get -0.8 suppression


def get_policy(family: str) -> EmissionPolicy:
    """Resolve the emission policy for a schema family."""
    return EmissionPolicy(family=family)
