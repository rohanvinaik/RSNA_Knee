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

from knee.absence import (  # noqa: F401  CODES: read by the post: lines
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
        # Recorded on BOTH paths: a stage that produced an empty map still ran, and a ledger with
        # no row for it cannot be told from a stage that never executed.
        ledger.record("ownership.produced", objects=0, claimed=0, residual=0)
        return empty_ownership(code, why)
    labels, available = arrays
    claims = labels != 0
    objects = np.unique(labels[claims]).size
    # The code names what the field held; the MAP is returned either way. A field that resolved
    # nothing is entirely residual, which is the reading worth looking at, not one to discard.
    code = ownership_code(predecessor_returned=True, item_count=objects)
    residual = available & ~claims
    ledger.record(
        "ownership.produced",
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
