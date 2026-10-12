"""Which places an `<object>` claims, which nothing claims, and which were never read.

OWNERSHIP's thin real implementation (`knee.ownership`). Its reason is the thesis's §10, which
here is the residual pull-out. The founder, 2026-10-11, on why the remainder is worth reading:
*"the roles that are still unassigned in the visual field are a lot easier to figure out, since
they're definitionally NOT the things you already DO know how to resolve."* This unit reads that
remainder off the interiors and counts it; it supplies no lens of its own.

**A partition, never an identification.** A non-zero label in `InteriorReading.labels` says only
that a place belongs to one resolved extent, and the extent is an integer index here. Membership
and individuation are all it claims: nothing in this module knows what any `<object>` is, and no
record names one. A place carries one label, so no place is claimed twice and this reading shows
no dispute between claims -- it does not invent one.

**Its picture is the residual map**: every place the acquisition read and nothing claims. The
residual is a distilled corpus and not a bucket, so `residual` stays a mask over the field and is
never folded into a count. A place the acquisition never read is neither claimed nor residual.
Unread is not unclaimed (`AGENTS.md` law 3: unknown is not false).

**What was not read is named, never defaulted.** `read_ownership` is total over its argument. A
missing reading is a silence, and a reading whose fields do not read as one (R,C) field is an
argument that cannot be read; both come back as the code `knee.absence` gives them, over empty
arrays, never a partial map. This module reads no bar: every value it inspects is a fact the
interiors already established, so there is no threshold here to argue about later.

**But a reading that CLAIMS NOTHING still returns its map, and that is the whole point.** Its code
is `predecessor_empty` — the predecessor returned a record and that record resolved no objects —
and the residual is then the entire field the acquisition read. `ownership/__init__.py` requires
exactly this: *"A round that claims nothing new hands back explicit unresolved material rather than
silently declaring the parse complete."* Returning an empty map there would lose the picture in the
case where the picture carries the most, so **the arrays are computed whenever the field is
READABLE, and the code names what was found in it.** A consumer therefore routes on `code` and
never on a count: `residual_places == 0` beside a non-`present` code is a reading that was not
made, not a field with no residual.
"""

from dataclasses import dataclass

import numpy as np

from knee.absence import (
    CODES,
    absence_code,
)
from knee.compute.contracts import ComputeContract, contracted, handed_on
from knee.telemetry import ledger

#: `absence_code` reads any count below zero as an argument that cannot be read.
UNREADABLE_COUNT = -1
CONTRACT = ComputeContract(
    kind="claimed_places_and_residual_map",
    language="NumPy vectorized reference; no accelerated twin",
    reads=(
        "labels integer (R,C), int32 from read_interiors: non-zero = claiming object "
        "index, zero = unclaimed; available bool (R,C), same shape; neither is written"
    ),
    writes=(
        "owned read-only bool claims and residual, (R,C) when present, else (0,0); "
        "int counts of claimed, residual and unread places and of objects; "
        "no identity of any object"
    ),
    allocation=(
        "O(N), N=R*C: two owned bool outputs, one bool temporary, O(K) scratch for the "
        "K<=N claimed labels; no whole-volume copy"
    ),
    work=(
        "fixed number of vectorized passes over the N places; one sort of the K claimed "
        "labels: O(N + K log K)"
    ),
    parallel_unit="plane (not concurrently enabled)",
    reference="read_ownership",
    proof_gate="intent/properties; real-entry corpus/pictures; no twin, so no SAME record",
)


@dataclass(frozen=True, slots=True)
class OwnershipReading:
    """One field partitioned into claimed, residual and unread places, with the code naming it.

    `claims` is True where a place carries a non-zero label, `residual` where a place was read
    and carries none; both are read-only (R,C) bool, and `objects` counts the distinct labels,
    each only an integer index.

    `code` is `present` when the field held claims, `predecessor_empty` when it held none — and
    the arrays are real in BOTH cases, because a field that resolved nothing is entirely residual
    and that is the reading worth looking at. Only a missing or unreadable argument yields an
    empty record, whose counts count nothing.

    `why` carries the predecessor's OWN named code forward, so the four distinct reasons
    `read_interiors` can resolve nothing (`empty_plane`, `no_finite_support`, `split_unavailable`,
    `no_interior_seeds`) do not collapse into one word here. It explains; it never decides.
    """

    code: str
    why: str
    claims: np.ndarray
    residual: np.ndarray
    claimed_places: int
    residual_places: int
    unavailable_places: int
    objects: int


def ownership_code(predecessor_returned: bool, item_count: int) -> str:
    """Name the absence this unit met, or `present` when it met none.

    `absence_code` with this unit's two constants. The unit is built, so `construction_absent`
    cannot arise here; the labels are read whenever a count exists, so `item_unread` cannot
    either. A count below zero is `absence_code`'s own word for an argument that cannot be read,
    which is `invalid_count` and names no silence.

    post: __return__ in CODES
    post: __return__ != "construction_absent"
    """
    return absence_code(
        construction_built=True,
        predecessor_returned=predecessor_returned,
        item_count=item_count,
        item_read=True,
    )


def readable_field(interiors: object) -> tuple[np.ndarray, np.ndarray] | None:
    """The labels and availability when they read as one (R,C) field; otherwise nothing.

    Integer labels over boolean availability of one shape. Anything else is an argument that
    cannot be read: coercing it would put a neighbouring reading in place of the one that was
    not made, and broadcasting mismatched shapes would hand back a wrong map without a word.
    """
    if interiors is None:
        return None
    labels = getattr(interiors, "labels", None)
    available = getattr(interiors, "available", None)
    if (
        isinstance(labels, np.ndarray)
        and isinstance(available, np.ndarray)
        and labels.ndim == 2
        and labels.shape == available.shape
        and labels.dtype.kind in "iu"
        and available.dtype.kind == "b"
    ):
        return labels, available
    return None


def empty_ownership(code: str, why: str) -> OwnershipReading:
    """The record that holds no places: the code that names why, over nothing at all.

    Only for an argument that is missing or cannot be read. A field that WAS read and claimed
    nothing is not this: it has a real residual map and returns one.
    """
    return OwnershipReading(
        code=code,
        why=why,
        claims=handed_on(np.zeros((0, 0), dtype=bool)),
        residual=handed_on(np.zeros((0, 0), dtype=bool)),
        claimed_places=0,
        residual_places=0,
        unavailable_places=0,
        objects=0,
    )


@contracted(CONTRACT)
def read_ownership(interiors: object) -> OwnershipReading:
    """Partition one field into claimed, residual and unread places, or name why it cannot.

    The intended argument is an `InteriorReading` or None, and the annotation is deliberately
    WIDER than that, as in `relations/shell.py`. The house requires this to be total and verified
    adversarially, so the malformed records its own tests pass it are part of the contract; a
    narrower annotation would declare a promise the tests themselves break, and `ty` said so.

    Total over its argument: nothing here raises. A reading that is missing, claims nothing or
    does not read as one field returns the empty record, with the code that names which it was.

    `read_interiors` labels only places it read, so claimed, residual and unread places sum to
    the field. A hand-built reading that labels an unread place is counted as both, as read:
    choosing between its two fields would be a guess, and this unit coins no code for it.

    post: __return__.code in CODES
    post: __return__.claims.shape == __return__.residual.shape
    """
    arrays = readable_field(interiors)
    if arrays is None:
        code = ownership_code(
            predecessor_returned=interiors is not None, item_count=UNREADABLE_COUNT
        )
        why = (
            "no interiors reading was handed to this stage"
            if interiors is None
            else "the interiors reading's labels and availability do not read as one (R,C) field"
        )
        # Recorded on BOTH paths: a member that produced an empty map still ran, and a ledger
        # with no row for it cannot be told from a member that never executed.
        ledger.record("ownership.member.produced", objects=0, claimed=0, residual=0)
        return empty_ownership(code, why)
    labels, available = arrays
    claims = labels != 0
    objects = np.unique(labels[claims]).size
    # The code names what the field held; the MAP is returned either way. A field that resolved
    # nothing is entirely residual, which is the reading worth looking at, not one to discard.
    code = ownership_code(predecessor_returned=True, item_count=objects)
    residual = available & ~claims
    ledger.record(
        "ownership.member.produced",
        objects=int(objects),
        claimed=int(np.count_nonzero(claims)),
        residual=int(np.count_nonzero(residual)),
    )
    return OwnershipReading(
        code=code,
        why=getattr(interiors, "code", ""),
        claims=handed_on(claims),
        residual=handed_on(residual),
        claimed_places=int(np.count_nonzero(claims)),
        residual_places=int(np.count_nonzero(residual)),
        unavailable_places=available.size - int(np.count_nonzero(available)),
        objects=objects,
    )


# ---------------------------------------------------------------------------------------------
# The members: one partition per PARSE, kept side by side (task 6.2, `specs/route-composition`).
#
# The conversation between same-orientation acquisitions returns, per series, two subdivisions of
# the solitary parse -- the concurrent one (barriers both acquisitions read) and the conditional one
# (barriers either read). Each is a labelling of the same field, so each is read with the SAME
# `read_ownership` and seated as a member, exactly as the lens stage seats its two populations.
# The founder, 2026-10-12: "we always keep information we compute. I'll resolve what we report and
# how we do it, but the pipeline should keep everything, including where things conflict." So no
# member is a fallback for another, no field names a winner, and the places where the solitary and
# concurrent claims differ are kept as a measurement -- the three-legged stool's informative case.
# ---------------------------------------------------------------------------------------------

#: The parses a member can read, in seating order. The solitary parse is always seated; the two
#: conversed parses are seated only where the conversation read the series.
PARSES: tuple[str, ...] = ("solitary", "concurrent", "conditional")

#: Every comparison standing between the solitary and concurrent members.
COMPARISONS: tuple[str, ...] = (
    "compared",
    "member_absent",
    "shape_mismatch",
    "invalid_count",
)

#: The conversation codes under which its subdivisions are a reading of this series' field.
CONVERSED_CODES: tuple[str, ...] = ("measured", "solitary")


@dataclass(frozen=True, slots=True)
class Parse:
    """One labelling of the field a member reads: its labels, availability, and the maker's code."""

    labels: np.ndarray
    available: np.ndarray
    code: str


@dataclass(frozen=True, slots=True)
class OwnershipMember:
    """One seated member: which parse it read, and its partition of the field."""

    parse: str
    reading: OwnershipReading


@dataclass(frozen=True, slots=True)
class OwnershipMembers:
    """Every seated member's partition, and where the first two disagree.

    `code` is `members_code` over the members' own codes; `why` says which parses were seated and
    why the others were not. `comparison` is `comparison_code` between the solitary and concurrent
    members; `disagreement` is the (R,C) mask where their claims differ, (0,0) unless compared, and
    `disagreeing_places` its count. Nothing here resolves a disagreement.
    """

    code: str
    why: str
    members: tuple[OwnershipMember, ...]
    comparison: str
    disagreement: np.ndarray
    disagreeing_places: int


def members_code(codes: tuple[str, ...]) -> str:
    """The stage's standing over its members' codes. Total over any tuple of strings.

    `present` when ANY member read a partition, because a body with one reading in it has a
    reading; otherwise the first member's own silence, which is the solitary parse's and names the
    predecessor. No members at all is `predecessor_absent`, and a code outside the shared
    vocabulary is `invalid_count` rather than a silence about the study.

    post: __return__ in CODES
    post: __return__ != "present" or "present" in codes
    post: __return__ != "predecessor_absent" or (not codes or codes[0] == "predecessor_absent")
    """
    if not codes:
        return "predecessor_absent"
    for code in codes:
        if code not in CODES:
            return "invalid_count"
    if "present" in codes:
        return "present"
    return codes[0]


def comparison_code(first_places: int, second_places: int, same_shape: bool) -> str:
    """Whether the solitary and concurrent claims can be compared place by place.

    A member holding no places (an empty record) cannot be compared; two fields of different
    shape cannot be compared; a negative count cannot be read at all.

    post: __return__ in COMPARISONS
    post: __return__ != "compared" or (first_places > 0 and second_places > 0 and same_shape)
    """
    if first_places < 0 or second_places < 0:
        return "invalid_count"
    if first_places == 0 or second_places == 0:
        return "member_absent"
    if not same_shape:
        return "shape_mismatch"
    return "compared"


def conversed_parses(interiors: object, conversation: object) -> tuple[Parse, ...]:
    """The conversation's subdivisions as parses of this field, or nothing when it did not read it.

    Seated only when the conversation's code says it read the series (`CONVERSED_CODES`) and its
    label maps have the field's shape; a `recipient_unavailable` conversation holds no reading of
    this field and seating its empty map would claim a field that resolved nothing.
    """
    code = getattr(conversation, "code", None)
    if code not in CONVERSED_CODES:
        return ()
    available = getattr(interiors, "available", None)
    if not isinstance(available, np.ndarray):
        return ()
    parses: list[Parse] = []
    for name in PARSES[1:]:
        labels = getattr(conversation, f"{name}_labels", None)
        if (
            isinstance(labels, np.ndarray)
            and labels.shape == available.shape
            and labels.dtype.kind in "iu"
        ):
            parses.append(Parse(labels, available, f"{name}:{code}"))
    return tuple(parses)


def read_ownership_members(interiors: object, conversation: object) -> OwnershipMembers:
    """Seat one member per parse the stages below produced, and keep where they disagree.

    Total over both arguments. The solitary parse is always seated, from the interiors; the
    conversed parses are seated when the conversation read this series. Each member is
    `read_ownership` over its parse, unchanged, so a member's code names the same silences it
    always did and the pure decision behind it is the one already pinned.

    post: __return__.code in CODES
    post: __return__.comparison in COMPARISONS
    post: len(__return__.members) >= 1
    """
    ledger.record(
        "objects.consumed_by.ownership",
        interiors=1 if readable_field(interiors) is not None else 0,
    )
    seated = [OwnershipMember("solitary", read_ownership(interiors))]
    conversed = conversed_parses(interiors, conversation)
    ledger.record("conversation.consumed_by.ownership", parses=len(conversed))
    seated.extend(
        OwnershipMember(parse.code.split(":")[0], read_ownership(parse))
        for parse in conversed
    )
    members = tuple(seated)
    first, second = (
        members[0].reading,
        (members[1].reading if len(members) > 1 else None),
    )
    comparison = comparison_code(
        first.claims.size,
        second.claims.size if second is not None else 0,
        second is not None and first.claims.shape == second.claims.shape,
    )
    if comparison == "compared" and second is not None:
        disagreement = handed_on(first.claims != second.claims)
    else:
        disagreement = handed_on(np.zeros((0, 0), dtype=bool))
    code = members_code(tuple(member.reading.code for member in members))
    if conversed:
        why = f"{len(members)} parses seated: " + ", ".join(m.parse for m in members)
    elif conversation is None:
        why = "solitary parse only: no conversation reading was handed to this stage"
    else:
        why = (
            "solitary parse only: the conversation did not read this series "
            f"({getattr(conversation, 'code', 'unreadable')})"
        )
    ledger.record(
        "ownership.produced",
        members=len(members),
        disagreeing=int(np.count_nonzero(disagreement)),
    )
    return OwnershipMembers(
        code=code,
        why=why,
        members=members,
        comparison=comparison,
        disagreement=disagreement,
        disagreeing_places=int(np.count_nonzero(disagreement)),
    )
