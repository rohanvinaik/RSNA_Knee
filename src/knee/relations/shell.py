"""THE RELATIONS: the sample-supported pairings this build retains, and the extent it still owes.

**What an interstice is.** The space between two `<object>`s, CONSTRUCTED and never detected. It
exists the moment its two bounding objects do, and it carries both their identities (the founder's
warrant is in `relations/__init__.py`). There is no search, no threshold and no name to recognise.

**What this stage consumes.** Task 1.3a's unit, `knee.relations.pairings.read_pairings`,
reconstructs the two existing sample sites flanking every bracketed dark run and retains, per
profile, the pair of indexed extents those samples support or the named refusal. Until the
composition repair of 2026-10-12 (`every-stage-renders` task 6.3) the route called that unit
BESIDE this shell and handed its result to nothing -- the Codex reading of the handoff: "the real
run retained 597 sample-supported pairs, but those records never reach this constructor". It is
now this stage's own reading: `read_relations` calls it and carries it as `pairings`, so whoever
holds the relations record holds every sample-supported pair and every refusal.

**What is still absent, and why `code` says so.** A sampled pair is SUPPORT for a relation, not the
relation: it says two extents face each other across one bracket on one selected plane, and
nothing about the extent of the space between them, its walls, its fill or its contents
(`specs/dark-bounded-pairing/spec.md`: "never as a continuous gap, volume, anatomical role or
complete interstice"). That construction is task 1.3a's second obligation and does not exist. So
`code` is `construction_absent` for EVERY argument, a perfectly good `InteriorReading` included:
the silence is about a unit missing from the build and not about the study, and a predecessor
code would blame the study for a gap in the build when the remedies are opposite.

**The record the construction will fill.** `Interstice` and `KINDS` are declared here, empty today,
so that the predicates stage reads ONE shape -- the kind of construction a finding's subject
requires, and the two indexed extents bounding it -- now and when the construction lands. A kind
is a structural tier of `docs/OBJECT_MODEL.md` (a facing pair's interstice, its content, a span,
the envelope, its lining) and never an anatomical word.

`interstices` is empty because nothing was constructed, and an empty tuple is NOT a finding of "no
interstice": a missing reading is silence, never a negative (`AGENTS.md` law 3). A consumer routes
on `code` and never on the length of the tuple. No pairing is invented, no threshold or bar is set,
and no zero stands in for a measurement that was not taken.

Record: `openspec/changes/every-stage-renders/`, tasks 1.3a, 1.3b and 6.3; `specs/stage-totality`,
`specs/dark-bounded-pairing`, `specs/route-composition`.
"""

from __future__ import annotations

from dataclasses import dataclass

from knee.absence import absence_code
from knee.objects.interiors import InteriorReading
from knee.relations.pairings import PairingReading, read_pairings
from knee.telemetry import ledger

#: The structural kinds of construction a relation can be: the object model's tiers by ROLE, never
#: by anatomy. A predicate names the kind its subject must satisfy and selects among the
#: constructions of that kind; the words here are the only vocabulary it may use.
KINDS: tuple[str, ...] = ("facing_pair", "content", "span", "envelope", "lining")

#: Why `construction_absent`, said once so the code and its reason cannot drift apart. The task
#: number and the words "has not been built" are load-bearing: the shell's tests read them.
WHY_ABSENT: str = (
    "The complete interstice extent (task 1.3a's second obligation) has not been built: "
    "sample-supported pairs across dark brackets are retained in `pairings`, but no record "
    "yet says the extent, walls, fill or contents of the space between two objects, so no "
    "interstice is constructed in this build."
)

#: Appended when the stage was handed something that does not read as an interiors reading, so
#: the absence of a pairing is explained rather than left as a bare None.
WHY_NOT_PAIRED: str = " The interiors reading handed over does not read as one, so no pairing was attempted."


@dataclass(frozen=True, slots=True)
class Interstice:
    """One constructed relation: its structural kind and the two indexed extents bounding it.

    `first` and `second` are `<object>` indices in the parse of `series_uid`; 0 means a side the
    construction could not resolve. `provenance` names the unit that constructed it. No field
    names anatomy. Nothing in this build constructs one yet: the shape is declared so that its
    consumer, the predicates stage, reads it today and reads the same thing when it lands.
    """

    kind: str
    first: int
    second: int
    series_uid: str
    provenance: str


@dataclass(frozen=True, slots=True)
class RelationsReading:
    """What the relations stage holds: the pairings it read, and the construction it did not make.

    `code` is a member of `CODES` in `absence.py`, and `why` says in one sentence what it names.
    In this build `code` is always `construction_absent` and `interstices` is always empty: an
    empty `interstices` means NOTHING WAS CONSTRUCTED and never "this study has no interstice".

    `pairings` is task 1.3a's sample-supported reading of the same predecessor, with its own code
    from the same vocabulary -- `present` when pairs were read, else which silence it met. It is
    None only when the stage was handed something that is not an interiors reading at all, and
    `why` then says so.
    """

    code: str
    why: str
    interstices: tuple[Interstice, ...]
    pairings: PairingReading | None = None


def read_relations(interiors: object, spacing_rc: object = None) -> RelationsReading:
    """Read the sample-supported pairings, and name the construction this build still owes.

    TOTAL over both arguments and it never raises: `None`, a perfectly good `InteriorReading` and
    a malformed object all receive `construction_absent`. The pairing unit is handed only an
    interiors reading or None, which it is total over; a malformed argument is recorded as a
    pairing that could not be attempted rather than passed on to raise.

    `absence_code` checks `construction_built` FIRST, so its other three arguments are provably
    unread. They are written as the neutral "nothing was taken" values rather than as sentinels,
    and whoever sets `construction_built=True` must supply real facts at this call site.

    post: __return__.code == "construction_absent"
    post: __return__.interstices == ()
    """
    readable = interiors is None or isinstance(interiors, InteriorReading)
    ledger.record(
        "objects.consumed_by.relations",
        interiors=1 if isinstance(interiors, InteriorReading) else 0,
    )
    pairings = read_pairings(interiors, spacing_rc) if readable else None
    paired = int(pairings.counts.get("paired", 0)) if pairings is not None else 0
    profiles = int(pairings.outcome_codes.size) if pairings is not None else 0
    ledger.record("pairings.consumed_by.relations", profiles=profiles, paired=paired)
    # Recorded even though it constructs nothing: a stage that is silent still ran, and a ledger
    # with no row for it cannot be told from a stage that never executed.
    ledger.record("relations.produced", interstices=0, pairs=paired)
    return RelationsReading(
        code=absence_code(
            construction_built=False,  # the one argument that is read
            predecessor_returned=interiors is not None,
            item_count=0,
            item_read=False,
        ),
        why=WHY_ABSENT if readable else WHY_ABSENT + WHY_NOT_PAIRED,
        interstices=(),
        pairings=pairings,
    )
