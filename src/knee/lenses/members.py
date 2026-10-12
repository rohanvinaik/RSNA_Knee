"""Where two seated members read the same place, what their standing is — kept, never resolved.

**Why it exists, against the thesis.** A lens is lossy by intent, so an `<object>` is a
superposition across lenses rather than a verdict from one. The founder, 2026-10-12: *"If there was
a single magical number that could somehow identify key objects in a view, then why are we here? ...
It's not a problem, it's the whole *point* of the thesis."* So where a reading can be made two
structurally warranted ways, both are made, and this names what the two said about one place.

**Why it NAMES dissent rather than settling it.** His ruling the same day: *"we always keep
information we compute. I'll resolve what we report and how we do it, but the pipeline should keep
everything, including where things conflict."* And 2026-10-10, the three-legged stool: *"when
sources of truth are defined as correct but are incomplete but overlapping in their coverage, then
the places in which they seem to disagree are not noise to wipe away, but are some of the MOST
informative information we can have."* Dissent is therefore a reading in its own right. This module
has no code meaning "resolved", and that absence is the design.

**Why a member's silence is not the other's problem.** `first_only` and `second_only` are readings,
not failures. A member that cannot place its edges is Abel Ackerman out sick; the body still sits
(`chapters/02-collapse/teachings.md`, THE CONCLAVE). Both second readers refuted the stronger claim
the lead had written — that a silence must never be caused by another member's absence — so nothing
here forbids a member depending on a shared measurement. It only forbids filling one member's
silence from the other, which would be a default, and project law 3 forbids a default.

Declared in `every-stage-renders` task 2.2a and the `ternary-place-digits` requirement "Every
structurally warranted population is a seated member, never a fallback".

This module reads no bar. Both arguments are codes a caller already decided, so there is no
threshold here to be argued about later.
"""

from __future__ import annotations

from knee.lenses.digits import DIGIT_CODES, is_read

#: Every standing this vocabulary admits. Note what is NOT here: no code means "resolved",
#: "preferred", "corrected" or "combined". Resolution is the founder's, never the pipeline's.
STANDING_CODES: tuple[str, ...] = (
    "concur",
    "dissent",
    "first_only",
    "second_only",
    "neither_read",
    "invalid_measurement",
)

#: The standings in which at least one member supplied a reading of this place.
READ_STANDINGS: tuple[str, ...] = ("concur", "dissent", "first_only", "second_only")


def standing_code(first: str, second: str) -> str:
    """Name what two seated members said about one place. Total over any pair of strings.

    `concur` and `dissent` both require two readings, and they are kept apart because their
    remedies differ: concurrence is confirmatory, dissent is the informative case the founder
    named, and collapsing them would discard exactly the signal the three-legged stool keeps.

    A code outside the digit vocabulary is `invalid_measurement` rather than a silence, for
    `absence_code`'s reason: an unreadable argument is a caller's fault, and naming it as a
    silence would turn that into a finding about the knee.

    post: __return__ in STANDING_CODES
    post: __return__ != "concur" or first == second
    post: __return__ != "dissent" or first != second
    post: __return__ not in ("concur", "dissent") or (is_read(first) and is_read(second))
    post: __return__ != "neither_read" or not (is_read(first) or is_read(second))
    """
    if first not in DIGIT_CODES or second not in DIGIT_CODES:
        return "invalid_measurement"
    first_read, second_read = is_read(first), is_read(second)
    if first_read and second_read:
        return "concur" if first == second else "dissent"
    if first_read:
        return "first_only"
    if second_read:
        return "second_only"
    return "neither_read"


def is_retained(code: str) -> bool:
    """Whether a standing carries a reading from at least one member.

    A caller counting coverage asks this. It is deliberately NOT "is this place resolved": a
    `dissent` is retained and is not resolved, and nothing in this module resolves it.

    post: __return__ == (code in READ_STANDINGS)
    """
    return code in READ_STANDINGS
