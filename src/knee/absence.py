"""The shared vocabulary of silences, so every stage names an absence the same way.

**Why it exists, against the thesis.** A missing reading is SILENCE, never a negative (`AGENTS.md`
law 3). The founder, 2026-10-10: *"'Silence' is meaningful, not a default negative score. That error
is a leak of ML priors to a structural AI approach."* A stage that is total over a missing
predecessor must therefore say WHICH silence it met, because the remedies differ — and a decision
returns a named code rather than a bool wherever two outcomes need different remedies.

**Why it is declared ONCE, before any stage that consumes it.** Fable, 2026-10-12, on the
breadth-first build: *"If each stage coins its own codes, the dependency graph passes vacuously
while the codes do not compose."* Three stages inventing three vocabularies would each pass their
own tests and compose with nothing, which is the failure this module is ordered first to prevent.

**The silences, each its own code because each has its own remedy:**

    predecessor_absent    the stage below returned nothing at all for this study
    predecessor_empty     it returned a record, and that record holds no items
    item_unread           the record holds items, and THIS one was not read
    construction_absent   a unit this stage needs has not been built -- not about an input at all

The fourth is not in `stage-totality`'s enumeration, which asks for "at least three", and it was
proved necessary twice. Fable found that the original `relations`/`ownership` shells needed a
silence that was none of the three; the lead then wrote that it dissolved once both stages went
real; and task 1.3a showed `relations` cannot go real until its facing-pair construction exists, so
the case came back. A stage that cannot run because a unit is missing is not reporting anything
about its input.

`present` names no silence. It completes the function, because the decision is TOTAL over its
arguments and must have an answer when there is no silence at all. `invalid_count` likewise names
an argument that cannot be read, rather than raising: a refusal is a verdict (`AGENTS.md` law 3).

This module reads no bar. Every value it inspects is a fact a caller already established, so there
is no threshold here to be argued about later.
"""

from __future__ import annotations

#: Every code this vocabulary admits. A stage never coins one outside it.
CODES: tuple[str, ...] = (
    "present",
    "construction_absent",
    "predecessor_absent",
    "predecessor_empty",
    "item_unread",
    "invalid_count",
)

#: The codes that name a silence. `present` is a reading; `invalid_count` is an unreadable argument.
SILENCES: tuple[str, ...] = (
    "construction_absent",
    "predecessor_absent",
    "predecessor_empty",
    "item_unread",
)


def absence_code(
    construction_built: bool,
    predecessor_returned: bool,
    item_count: int,
    item_read: bool,
) -> str:
    """Name the silence a stage met, or `present` when it met none.

    The order is the order of causes, and `construction_built` is checked FIRST deliberately. A
    stage whose own unit has not been built cannot consume anything, so it reports that and says
    nothing about its input: answering `predecessor_absent` there would blame the study for a gap
    in the build, and the two have opposite remedies -- one is "build the unit", the other is "this
    study has no such reading".

    `invalid_count` is kept distinct from `predecessor_empty` for the same reason. A count below
    zero is an argument that cannot be read; a count of zero is a record that was read and held
    nothing. Collapsing them would turn a caller's bug into a finding about the knee.

    post: __return__ in CODES
    """
    if not construction_built:
        return "construction_absent"
    if not predecessor_returned:
        return "predecessor_absent"
    if item_count < 0:
        return "invalid_count"
    if item_count == 0:
        return "predecessor_empty"
    if not item_read:
        return "item_unread"
    return "present"


def is_silence(code: str) -> bool:
    """Whether a code names a silence, for a caller routing on the distinction.

    `present` is a reading and `invalid_count` is an unreadable argument; neither is a silence, and
    an unknown string is not one either -- this answers only for the vocabulary it owns.

    post: __return__ == (code in SILENCES)
    """
    return code in SILENCES
