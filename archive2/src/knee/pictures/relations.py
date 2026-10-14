"""Arrange the relations stage's existing values in a construction-status frame.

Task 1.3b, extended by task 6.3, of ``openspec/changes/every-stage-renders``. The frame
reports pipeline construction status, not study-derived relation evidence: the stage's
``construction_absent`` code names the missing interstice extent. An empty ``interstices``
tuple does not assert that a study has no interstice. The pairing reading the stage now
carries is passed through beside it, unchanged, so a drawer can show what IS retained
(``knee.pictures.pairings`` arranges that record's own values).

Following thesis §13.7, this picture layer only arranges the completed reading's ``code``,
``why``, ``interstices`` and ``pairings``. It constructs no interstice, takes no
measurement and makes no decision. The workbench draws the returned frame.
"""

from __future__ import annotations

from dataclasses import dataclass

from knee.relations.pairings import PairingReading
from knee.relations.shell import RelationsReading


@dataclass(frozen=True, slots=True)
class RelationsPanels:
    """The relations reading's unchanged values, ready for the workbench to draw."""

    code: str
    why: str
    interstices: tuple
    pairings: PairingReading | None = None


def panels(reading: RelationsReading) -> RelationsPanels:
    """Hand on the existing status, reason, interstices and pairings without interpreting them."""
    return RelationsPanels(
        code=reading.code,
        why=reading.why,
        interstices=reading.interstices,
        pairings=reading.pairings,
    )
