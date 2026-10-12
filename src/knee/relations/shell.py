"""THE RELATIONS, as a SHELL: it runs, and it names the one unit it is waiting for.

**What an interstice is.** The space between two `<object>`s, CONSTRUCTED and never detected.
It exists the moment its two bounding objects do, and it carries both their identities (the
founder's warrant is in `relations/__init__.py`). There is no search, no threshold and no name
to recognise.

**Identity was never the blocker.** An interstice needs the PAIR of objects that bound it, and
nothing in making one asks what either object IS. What blocks this stage is a record that does
not exist.

**The missing record: which two objects face each other.** In `objects/interiors.py`,
`boundary_edges` does `regions.append(labels[rows, cols])`, the territory's OWN label, and reads
the neighbour only to decide THAT a place is an edge and of which KIND, as in
`kind[padded[nr, nc] > 0] = EDGE_KINDS["peer_territory"]`. So the far side of every boundary is
unrecorded. For the pairs wanted here, storing the neighbour's label would not repair that: they
are bounded ACROSS a dark band (`tasks.md`, 1.3a), and `read_interiors` labels only
`interior = available & ~dark`, so the neighbour of a `low_signal` edge is a dark place whose
label is 0. `dark_bands` records where a band lies (`trace`, a position) and never which
territory a profile reached beyond it. Task 1.3a ("Record which territory each bracketed profile
reached across the dark") is that construction. It is its own unit, and it does not exist yet.

**So this stage runs and says so**, rather than returning nothing, raising, or guessing a
pairing. `read_relations` answers `construction_absent` (`absence.py`) for EVERY argument, a
perfectly good `InteriorReading` included. That is deliberate. The silence is about a unit
missing from the build and not about the input, and a predecessor code would blame the study for
a gap in the build, when the remedies are opposite: "build the unit" against "this study has no
such reading". It is none of the three input silences, since it is not about an input at all.

`interstices` is empty because nothing was constructed, and an empty tuple is NOT a finding of
"no interstice": a missing reading is silence, never a negative (`AGENTS.md` law 3). A consumer
routes on `code` and never on the length of the tuple. No pairing is invented, no threshold or
bar is set, and no zero stands in for a measurement that was not taken.

This is task 1.3b. It stays a shell until task 1.3a lands, and that task removes it.

Record: `openspec/changes/every-stage-renders/`, tasks 1.3a and 1.3b, and `specs/stage-totality`.
"""

from __future__ import annotations

from dataclasses import dataclass

from knee.absence import absence_code

#: Why `construction_absent`, said once so the code and its reason cannot drift apart.
WHY_ABSENT: str = (
    "The facing-pair construction (task 1.3a) has not been built: no record says "
    "which two objects face each other across a border, so no interstice is "
    "constructed in this build."
)


@dataclass(frozen=True, slots=True)
class RelationsReading:
    """What the relations stage read, or the named silence it met instead.

    `code` is a member of `CODES` in `absence.py`, and `why` says in one sentence what it
    names. In this build `code` is always `construction_absent` and `interstices` is always
    empty. An empty `interstices` means NOTHING WAS CONSTRUCTED; it never means "this study has
    no interstice", so a consumer routes on `code` and never on the length of the tuple.
    """

    code: str
    why: str
    interstices: tuple


def read_relations(interiors: object) -> RelationsReading:
    """Name the silence of a stage whose facing-pair construction has not been built.

    TOTAL over `interiors`, and it never raises: `None`, a perfectly good `InteriorReading` and
    a malformed object all receive the same answer, `construction_absent`. The argument is
    accepted so the route can call this stage now, and it is tested for `None` and nothing more.

    `absence_code` checks `construction_built` FIRST, so the other three arguments are **provably
    unread** — no value of any of them can change the answer, which is the point. None of them is
    therefore a claim about the input, and none should be read as one. They are written as the
    neutral "nothing was taken" values rather than as a sentinel: a `-1` would borrow
    `invalid_count`, whose meaning is "the caller supplied a count I cannot read", to say "no count
    was taken", and the vocabulary's integrity is worth more than a defensive hypothetical. When
    task 1.3a lands, whoever sets `construction_built=True` must supply real facts at this same
    call site, and the must-not test below is what refuses the answer changing before then.

    post: __return__.code == "construction_absent"
    post: __return__.interstices == ()
    """
    return RelationsReading(
        code=absence_code(
            construction_built=False,  # the one argument that is read
            predecessor_returned=interiors is not None,
            item_count=0,
            item_read=False,
        ),
        why=WHY_ABSENT,
        interstices=(),
    )
