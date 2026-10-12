"""Arrange the relations shell's existing values in a construction-status frame.

This is task 1.3b of ``openspec/changes/every-stage-renders``. The frame reports
pipeline construction status, not study-derived relation evidence: the shell's
``construction_absent`` code names the missing facing-pair construction. An empty
``interstices`` tuple does not assert that a study has no interstice.

Following thesis §13.7, this picture layer only arranges the completed reading's
``code``, ``why`` and ``interstices``. It constructs no interstice, takes no
measurement and makes no decision. The workbench draws the returned frame.
"""

from __future__ import annotations

from dataclasses import dataclass

from knee.relations.shell import RelationsReading


@dataclass(frozen=True, slots=True)
class RelationsPanels:
    """The relations reading's unchanged values, ready for the workbench to draw."""

    code: str
    why: str
    interstices: tuple


def panels(reading: RelationsReading) -> RelationsPanels:
    """Hand on the existing status, reason and interstices without interpreting them."""
    return RelationsPanels(
        code=reading.code,
        why=reading.why,
        interstices=reading.interstices,
    )
