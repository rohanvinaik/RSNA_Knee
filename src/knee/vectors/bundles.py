"""THE BUNDLES (§7, §13): an `<object>`'s profile as row counts over named banks.

Task 6.7 of `every-stage-renders`, the first increment of §3, under `specs/object-bundles/spec.md`.
The founder settled the shape on 2026-10-11 from the thesis's own figures H2a2 and H2b: a profile
is **row counts over named banks**, every row one balanced-ternary digit against a middle, and a
bank this build cannot write is carried as a **named unavailable status, never as rows of zero**,
because a zero count asserts a reading was made and found nothing.

**The dispatch answer, recorded before the body** (`tasks.md`, "The dispatch question"): the
subject this stage keys a profile on is the INDEXED EXTENT of the selected native plane, which
ownership's solitary member resolved from `interiors.labels`. That is a relational fact an
earlier stage computed, not a kind-label, so the task proceeds; `subject_kind` is written into
the record so a consumer handed a territory-keyed profile can abstain rather than take the
territory for a named object.

**The banks, each naming the stage its quantity came from:**

    own_reading:<member>   counts over the lens digit codes at the object's places, one bank per
                           seated lens member, from `knee.lenses` (the selected plane only)
    lens_standing          counts over what the two members jointly said at those places
    came_out               how the object came out: counts over its edge kinds and its profile
                           trace codes, and its seeds (the places of the h-maxima plateaus it grew
                           from, counted inside its extent), from `knee.objects` (the provenance
                           bank, §6.6)
    through_plane:<uid>    for every OTHER acquisition of the study, counts over `SLAB_CODES` of
                           whether that acquisition's slabs measured each of this object's places
                           -- the slab rule's first consumer, and the geometric precondition of
                           any conjunction across acquisitions. The rule is called through its
                           array twin (`knee.lenses.slab_kernels`: a plain reference or a Numba
                           twin), selected by the backend the request names and refused by name
                           when unavailable, never replaced; the scalar rule
                           (`knee.lenses.slabs.slab_code`) stays the oracle the twin is pinned to

**Beside the banks, one number per other acquisition** (`BundlesReading.slab_gaps`, task 7.2): the
gap fraction of that acquisition's own stack, `knee.lenses.slabs.gap_fraction(thickness, pitch)`,
which "belongs beside a conjunction as the prior probability that a foreign place falls into
nothing". It is a property of the ACQUISITION and not a count at the object's places, so it is
recorded on the reading beside the through-plane banks and not inside one. It uses the same pitch
the through-plane bank does, and it is None where the thickness or the slice geometry was not read
or is not one the function accepts, never a zero standing in for a reading not made.

**Banks this build cannot write, carried as unavailable with the reason:** the conjunction across
acquisitions (needs the local structural normalisation and a correspondence rule, both the
founder's), the composite, the dome link and the ring (no knee version given).

One plane is read, and the record says so; nothing here claims depth, volume or continuity.
Nothing here derives an identity, an admission or a resemblance from a profile.

The body is in `read_bundles` below; its contract, record shape and intent tests are the lead's.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass

import numpy as np

from knee.absence import absence_code, is_silence
from knee.collapse.physical import PlaneFrame
from knee.compute.contracts import ComputeContract, contracted, handed_on
from knee.lenses.digits import DIGIT_CODES
from knee.lenses.members import STANDING_CODES
from knee.lenses.places import MEMBERS
from knee.lenses.slab_kernels import slab_codes
from knee.lenses.slabs import SLAB_CODES, gap_fraction
from knee.objects.interiors import EDGE_KINDS, TRACE_CODES
from knee.telemetry import ledger

#: Every code this stage admits for the stage and for a bank.
CODES: tuple[str, ...] = (
    "present",
    "construction_absent",
    "predecessor_absent",
    "predecessor_empty",
    "item_unread",
    "invalid_count",
)

#: A bank's status: written from the quantity it names, or unavailable with the reason.
BANK_STATUS: tuple[str, ...] = ("written", "unavailable")

#: The banks the design names that this build cannot write, each with the reason, so they appear
#: in every profile as unavailable rather than being silently omitted.
UNAVAILABLE_BANKS: tuple[tuple[str, str], ...] = (
    (
        "conjunction_across_acquisitions",
        "needs the local structural normalisation and a correspondence rule, both the founder's",
    ),
    ("composite", "no knee version of the composite has been given"),
    ("dome_link", "no knee version of the dome link has been given"),
    ("ring", "no knee version of the ring has been given"),
)

SUBJECT_KIND: str = "indexed_extent_of_the_selected_native_plane"


@dataclass(frozen=True, slots=True)
class Bank:
    """One bank of a profile: its name, where its quantity came from, and its rows or its absence.

    `rows` maps a row name to a whole count and is empty when `status` is `unavailable`; a zero
    count can only mean the reading was made and found nothing.
    """

    name: str
    source_stage: str
    status: str
    rows: Mapping[str, int]
    why: str


@dataclass(frozen=True, slots=True)
class ObjectProfile:
    """One `<object>`'s profile: its index, how many places wrote it, and every bank by name."""

    index: int
    places: int
    banks: tuple[Bank, ...]


@dataclass(frozen=True, slots=True)
class BundlesReading:
    """Every object's profile for one series, with what the profiles were keyed on and read from.

    `subject_kind` is `SUBJECT_KIND`; `planes_read` is 1 because the selected native plane is the
    only plane the partition exists on. `code` is from the shared vocabulary. `backend` is the
    backend the through-plane banks were REQUESTED to use, recorded on every path, silences
    included, so a reading never claims a kernel nobody asked for or hides one that was refused.
    `slab_gaps` holds one `(series uid, gap fraction)` pair per OTHER acquisition, in the order
    they were handed over; a fraction is None where it could not be read, and the tuple is empty
    on a silence, which read no acquisition.
    """

    code: str
    why: str
    subject_kind: str
    planes_read: int
    profiles: tuple[ObjectProfile, ...]
    backend: str = "reference"
    slab_gaps: tuple[tuple[str, float | None], ...] = ()


def bank_status_code(source_present: bool, rows_countable: bool) -> str:
    """Whether a bank may be written: only when its source stage's quantity is present and counts.

    post: __return__ in BANK_STATUS
    post: __return__ != "written" or (source_present and rows_countable)
    """
    return "written" if source_present and rows_countable else "unavailable"


# ---------------------------------------------------------------------------------------------
# The body (task 6.7). A profile is a slice of tables: each bank counts ONE quantity at the
# claimed places of the selected plane for ALL extents at once, and extent u's profile is row u of
# every table, so nothing is recounted per object. Nothing below names what an extent is.
# ---------------------------------------------------------------------------------------------

CONTRACT = ComputeContract(
    kind="per_extent_value_counts",
    language=(
        "NumPy vectorized reference, one bincount per bank; the through-plane banks call the "
        "slab rule through its array twin (knee.lenses.slab_kernels: Python reference or Numba "
        "strict twin), selected by the requested backend, refused by name and never replaced"
    ),
    reads=(
        "extent int (N,) dense extent index 0..U-1 of each claimed place; values int (N,) "
        "non-negative readings below the vocabulary; U and the vocabulary width as whole numbers"
    ),
    writes=(
        "owned read-only int64 (U, vocabulary) table of whole counts, row u = extent u's rows; "
        "no input written; no identity of any extent"
    ),
    allocation=(
        "N int64 combined index plus the U*vocabulary table; "
        "no copy of the plane or of the lens maps"
    ),
    work=(
        "kernel: one bincount pass over the N claimed places per bank, O(N + U*vocabulary). "
        "Stage: each through-plane bank also evaluates the slab rule once per claimed place for "
        "each other acquisition it is written against, N evaluations through the array twin, "
        "counted in the ledger as slab_places on vectors.produced; an acquisition whose bank is "
        "unavailable evaluates nothing and adds none. Each other acquisition also gets one "
        "gap_fraction read from its own stack, O(slices), recorded on the reading as slab_gaps"
    ),
    parallel_unit="selected plane (not concurrently enabled)",
    reference=(
        "count_by_extent; the slab rule's kernel is slab_codes_reference in "
        "knee.lenses.slab_kernels, pinned element by element to the scalar slab_code, which "
        "stays the oracle"
    ),
    proof_gate=(
        "direct intent tests against np.bincount of each extent's mask; "
        "real-entry receipt and picture"
    ),
)


@contracted
def count_by_extent(
    extent: np.ndarray, values: np.ndarray, extents: int, vocabulary: int
) -> np.ndarray:
    """Count, for every extent at once, how many of its places carry each value.

    `extent[i]` is place i's dense extent index and `values[i]` its reading, a whole number below
    `vocabulary`; both are 1-D and equally long, and every index is below `extents`. Row u of the
    result is extent u's rows, so an extent none of whose places carries a value is a row of
    zeros: a reading that was made and found nothing, which the caller only asks for where the
    quantity existed. The result is owned and read-only, and nothing is written to the inputs.

    This is a kernel and not a decision, so it states what it needs rather than being total: the
    stage checks every one of these before it calls, and names a bank unavailable when one fails.

    pre: extents >= 0
    pre: vocabulary >= 1
    pre: len(extent) == len(values)
    pre: all(0 <= int(e) < extents for e in extent)
    pre: all(0 <= int(v) < vocabulary for v in values)
    post: __return__.shape == (extents, vocabulary)
    post: int(__return__.sum()) == len(extent)
    """
    flat = extent.astype(np.int64) * vocabulary + values.astype(np.int64)
    table = np.bincount(flat, minlength=extents * vocabulary)
    return handed_on(table.reshape(extents, vocabulary))


def stage_code(
    ownership_code: str, subject_returned: bool, subject_readable: bool, extents: int
) -> str:
    """The stage's own code: ownership's silence when it is not `present`, else the field's.

    Ownership says whether any object was individuated; the interiors then say whether the extents
    can be read. A silence, as `knee.absence.is_silence` names it, is passed on unchanged, so
    `predecessor_empty` from a field that claimed nothing stays `predecessor_empty` and is never
    renamed. Any other code that is not `present` -- `invalid_count` itself, or a string outside the
    shared vocabulary -- is `invalid_count`, an argument that cannot be read, and never a silence
    about the study. `present` needs ownership present, the interiors handed over, their labels
    readable and at least one extent.

    post: __return__ in CODES
    post: __return__ != "present" or (ownership_code == "present" and subject_returned and subject_readable and extents > 0)
    """
    if is_silence(ownership_code):
        return ownership_code
    if ownership_code != "present":
        return "invalid_count"
    return absence_code(
        construction_built=True,
        predecessor_returned=subject_returned,
        item_count=extents if subject_readable else -1,
        item_read=True,
    )


@dataclass(frozen=True, slots=True)
class _Count:
    """One bank's quantity for EVERY extent: its status, its table and its reason.

    `table` is (extents, len(names)) whole counts when `status` is `written` and None otherwise;
    row u of it is extent u's rows. `why` says what was counted, or what was missing.
    """

    name: str
    source_stage: str
    names: tuple[str, ...]
    status: str
    table: np.ndarray | None
    why: str


def _silence(code: str, why: str, backend: str) -> BundlesReading:
    """The reading that holds no profile, naming the silence met and the backend asked for."""
    return BundlesReading(
        code=code,
        why=why,
        subject_kind=SUBJECT_KIND,
        planes_read=1,
        profiles=(),
        backend=backend,
    )


def _ownership_standing(ownership: object) -> str:
    """The code ownership returned, or the silence that stands for it when it returned nothing.

    post: __return__ in CODES
    """
    if ownership is None:
        return "predecessor_absent"
    code = getattr(ownership, "code", None)
    return code if isinstance(code, str) and code in CODES else "invalid_count"


def _ownership_why(ownership: object, code: str) -> str:
    """Why no profile was written when ownership individuated nothing it could stand behind."""
    if ownership is None:
        return (
            "no ownership reading was handed to this stage, so no object is individuated "
            "and no profile is written"
        )
    if getattr(ownership, "code", None) == code:
        return f"ownership returned {code}, so no object is individuated and no profile is written"
    return "the ownership reading does not read as one record, so no profile is written"


#: Why the field could not be read, by the code `stage_code` gave once ownership was present.
_SUBJECT_WHY: dict[str, str] = {
    "predecessor_absent": (
        "ownership individuated objects but the objects stage handed this stage no interiors "
        "reading, so the extents cannot be read"
    ),
    "invalid_count": (
        "the interiors' labels do not read as one (R,C) field of non-negative whole numbers, "
        "so the extents cannot be read"
    ),
    "predecessor_empty": "the interiors' labels claim no place, so there is no extent to profile",
}


def _seated(ownership: object) -> str:
    """Which parses ownership seated, as it named them; the profiles are keyed on the solitary one."""
    members = getattr(ownership, "members", None)
    if not isinstance(members, (tuple, list)):
        return "not read"
    parses = [getattr(member, "parse", None) for member in members]
    named = [parse for parse in parses if isinstance(parse, str)]
    return ", ".join(named) if named else "not read"


def _labels(interiors: object) -> np.ndarray | None:
    """The interiors' labels when they read as one (R,C) field of non-negative whole numbers."""
    labels = getattr(interiors, "labels", None)
    if not (
        isinstance(labels, np.ndarray)
        and labels.ndim == 2
        and labels.dtype.kind in "iu"
    ):
        return None
    if labels.size and labels.dtype.kind == "i" and int(labels.min()) < 0:
        return None
    return labels


def _plane_index(measurements: object) -> int | None:
    """The selected plane's index into the lens maps, or None when it does not read as one."""
    index = getattr(measurements, "slice_index", None)
    whole = isinstance(index, (int, np.integer)) and not isinstance(index, bool)
    return int(index) if whole and index >= 0 else None


def _plane_of(
    maps: object, plane: int | None, shape: tuple[int, ...]
) -> np.ndarray | None:
    """The selected plane of a (Z,R,C) integer map when it is a map of THIS field, else None."""
    if not (
        isinstance(maps, np.ndarray) and maps.ndim == 3 and maps.dtype.kind in "iu"
    ):
        return None
    if plane is None or plane >= maps.shape[0] or maps.shape[1:] != shape:
        return None
    return maps[plane]


def _within(values: np.ndarray, vocabulary: int) -> bool:
    """Whether every value is a row of the vocabulary: a whole number in 0..vocabulary-1."""
    if values.dtype.kind not in "iu":
        return False
    if not values.size:
        return True
    non_negative = values.dtype.kind == "u" or int(values.min()) >= 0
    return non_negative and int(values.max()) < vocabulary


def _count_plane(
    name: str,
    source_stage: str,
    names: tuple[str, ...],
    values: np.ndarray | None,
    extent_of: np.ndarray,
    extents: int,
    unread: str,
    written: str,
) -> _Count:
    """One plane-valued bank: the gathered values counted per extent, or the reason it cannot be.

    `values` is the quantity at the claimed places, or None when its source was absent. The status
    is decided by `bank_status_code` from two facts and no others -- the source is present, and
    every value is a row of the vocabulary. It is never decided from a member's own code: a member
    that could not place its edges still READ every place as `no_edges`, which is a row, so its
    silence is a written bank of named silences and never an absent one.
    """
    present = values is not None
    countable = values is not None and _within(values, len(names))
    status = bank_status_code(present, countable)
    if values is not None and status == "written":
        table = count_by_extent(extent_of, values, extents, len(names))
        return _Count(name, source_stage, names, status, table, written)
    why = (
        unread
        if values is None
        else f"a value of {name} falls outside its {len(names)} named rows"
    )
    return _Count(name, source_stage, names, status, None, why)


def _lens_unread(lenses: object, plane: int | None) -> str:
    """Why a lens map could not be read at the selected plane."""
    if lenses is None:
        return "no lens record was handed to this stage"
    if plane is None:
        return (
            "the objects stage named no readable plane index, so no lens map can be read "
            "at the selected plane"
        )
    return "the lens map does not read as the selected plane of this field"


def _member_name(member: object, index: int) -> str:
    """A seated member's population as it named itself, or a stable name for an unreadable one."""
    population = getattr(member, "population", None)
    if isinstance(population, str) and population:
        return population
    return f"unread_member_{index}"


def _lens_counts(
    lenses: object,
    plane: int | None,
    shape: tuple[int, ...],
    claimed: np.ndarray,
    extent_of: np.ndarray,
    extents: int,
) -> list[_Count]:
    """One own-reading bank per seated member, then what the members jointly said.

    With no readable member list the banks are still NAMED, from the seats the lens stage declares,
    and carried unavailable: a bank that vanished would read as a reading nobody was asked for.
    """
    members = getattr(lenses, "members", None)
    if isinstance(members, (tuple, list)):
        seated = [
            (_member_name(member, index), getattr(member, "codes", None))
            for index, member in enumerate(members)
        ]
    else:
        seated = [(population, None) for population, _, _ in MEMBERS]
    unread = _lens_unread(lenses, plane)
    counts = []
    for population, codes in seated:
        picked = _plane_of(codes, plane, shape)
        counts.append(
            _count_plane(
                f"own_reading:{population}",
                "lenses",
                DIGIT_CODES,
                None if picked is None else picked[claimed],
                extent_of,
                extents,
                unread,
                f"counts of {population}'s digit codes at this object's places on the "
                "selected plane",
            )
        )
    standing = _plane_of(getattr(lenses, "standings", None), plane, shape)
    counts.append(
        _count_plane(
            "lens_standing",
            "lenses",
            STANDING_CODES,
            None if standing is None else standing[claimed],
            extent_of,
            extents,
            unread,
            "counts of what the seated members jointly said at this object's places on the "
            "selected plane",
        )
    )
    return counts


def _edge_list(interiors: object, name: str) -> np.ndarray | None:
    """One of the objects stage's per-edge records when it reads as a 1-D list of whole numbers."""
    array = getattr(interiors, name, None)
    if isinstance(array, np.ndarray) and array.ndim == 1 and array.dtype.kind in "iu":
        return array
    return None


def _edge_arrays(
    interiors: object,
) -> tuple[np.ndarray, np.ndarray, np.ndarray] | None:
    """The objects stage's edge regions, kinds and trace codes when they read as three equal lists."""
    regions = _edge_list(interiors, "edge_regions")
    kinds = _edge_list(interiors, "edge_kinds")
    traces = _edge_list(interiors, "trace_codes")
    if regions is None or kinds is None or traces is None:
        return None
    if not regions.shape == kinds.shape == traces.shape:
        return None
    return regions, kinds, traces


def _markers(interiors: object, shape: tuple[int, ...]) -> np.ndarray | None:
    """The objects stage's markers when they read as one integer or boolean field of this shape."""
    markers = getattr(interiors, "markers", None)
    if (
        isinstance(markers, np.ndarray)
        and markers.shape == shape
        and markers.dtype.kind in "biu"
    ):
        return markers
    return None


def _came_out(
    interiors: object,
    claimed: np.ndarray,
    extent_labels: np.ndarray,
    extent_of: np.ndarray,
    extents: int,
) -> _Count:
    """How each object came out: its edges by kind and trace code, and its seeds, from the objects stage.

    The provenance bank (§6.6). An edge is attributed to an extent through `edge_regions`, the label
    of the claimed place the edge leaves, and every region must be one of the extents profiled: an
    edge naming a region the labels do not hold is a record that disagrees with itself, and the
    bank is then carried unavailable rather than counted over a subset.

    The seeds (task 3.2) are the places inside the extent where `markers` is non-zero: the h-maxima
    plateaus the territory grew from. They are gathered at the claimed places, in the order every
    other bank uses, so `extent_of` indexes them. Markers that are not an integer or boolean field
    of the labels' shape cannot be counted, and then the WHOLE bank is carried unavailable and names
    the markers, whether or not the edges also failed: a seeds row of zeros would assert a reading
    that was never made.
    """
    names = (
        tuple(f"edge_kind:{name}" for name in EDGE_KINDS)
        + tuple(f"trace:{name}" for name in TRACE_CODES)
        + ("seeds",)
    )
    written = (
        "counts of this object's edges by kind and by profile trace code, and of the seed "
        "places it grew from, from the objects stage"
    )
    edges = _edge_arrays(interiors)
    markers = _markers(interiors, claimed.shape)
    if edges is None or markers is None:
        unread: list[str] = []
        if edges is None:
            unread.append(
                "the objects stage's edge records were not handed over as three equal integer lists"
            )
        if markers is None:
            unread.append(
                "the objects stage's markers were not handed over as an integer or boolean "
                "field of the labels' shape, so its seeds cannot be counted"
            )
        return _Count(
            "came_out",
            "objects",
            names,
            bank_status_code(False, False),
            None,
            "; ".join(unread),
        )
    regions, kinds, traces = edges
    where = np.searchsorted(extent_labels, regions)
    held = (where < extent_labels.size) & (
        extent_labels[np.minimum(where, extent_labels.size - 1)] == regions
    )
    countable = bool(
        held.all()
        and np.isin(kinds, tuple(EDGE_KINDS.values())).all()
        and np.isin(traces, tuple(TRACE_CODES.values())).all()
    )
    status = bank_status_code(True, countable)
    if status != "written":
        return _Count(
            "came_out",
            "objects",
            names,
            status,
            None,
            "the objects stage's edges name a region or a code outside what it declares",
        )
    by_kind = count_by_extent(where, kinds, extents, max(EDGE_KINDS.values()) + 1)
    by_trace = count_by_extent(where, traces, extents, max(TRACE_CODES.values()) + 1)
    seeded = count_by_extent(
        extent_of, (markers[claimed] != 0).astype(np.uint8), extents, 2
    )
    table = np.concatenate(
        (
            by_kind[:, list(EDGE_KINDS.values())],
            by_trace[:, list(TRACE_CODES.values())],
            seeded[:, 1:],
        ),
        axis=1,
    )
    return _Count("came_out", "objects", names, status, handed_on(table), written)


def _places_in_patient(frame: object, claimed: np.ndarray) -> np.ndarray | None:
    """The claimed places' centres in the patient's frame (N,3), in the order `claimed` gathers them.

    None when this plane's frame is not one the frame type owns or cannot place them.
    """
    if not isinstance(frame, PlaneFrame):
        return None
    rows, columns = np.nonzero(claimed)
    with np.errstate(all="ignore"):
        try:
            return frame.to_patient(np.column_stack((rows, columns)).astype(np.float64))
        except (ValueError, TypeError):
            return None


def _finite(value: object) -> float | None:
    """A finite real number as a float; None for anything else, NaN included.

    NaN is how this codebase says a reading was not made, so it is not a thickness of any size.
    """
    if isinstance(value, bool) or not isinstance(
        value, (int, float, np.integer, np.floating)
    ):
        return None
    number = float(value)
    return number if np.isfinite(number) else None


def _stack(
    geometry: object,
) -> tuple[np.ndarray, np.ndarray, np.ndarray] | None:
    """An acquisition's slice normal (3,), slice positions (n,3) and their heights along it (n,).

    None unless all three read as one finite stack of at least one slice.
    """
    found = tuple(
        getattr(geometry, name, None) for name in ("normal", "position", "along_normal")
    )
    if not all(
        isinstance(array, np.ndarray) and array.dtype.kind in "iuf" for array in found
    ):
        return None
    normal, position, heights = (np.asarray(array, dtype=np.float64) for array in found)
    if (
        normal.shape != (3,)
        or position.ndim != 2
        or position.shape[1] != 3
        or heights.ndim != 1
        or heights.shape[0] != position.shape[0]
        or not heights.size
    ):
        return None
    if not all(np.isfinite(array).all() for array in (normal, position, heights)):
        return None
    return normal, position, heights


def _pitch(centres: np.ndarray, thickness: float) -> float:
    """An acquisition's pitch: the median gap between its slice centres, or its thickness for one.

    `centres` are the slice heights along the normal, sorted ascending. With a single slice the
    pitch is taken to be the thickness, so that no gap exists. The ONE derivation, used by the
    through-plane codes and by the gap fraction alike. Callers hold `np.errstate`: heights large
    enough to overflow a difference make an infinite pitch, which the slab rule and `gap_fraction`
    each refuse by name.
    """
    return float(np.median(np.diff(centres))) if centres.size >= 2 else thickness


def _slab_codes(
    place_lps: np.ndarray,
    stack: tuple[np.ndarray, np.ndarray, np.ndarray],
    frame: PlaneFrame,
    shape: tuple[int, ...],
    thickness: float,
    backend: str,
) -> np.ndarray | None:
    """The slab code of every place against ONE other acquisition, as indices into SLAB_CODES.

    Each place is matched to the nearest slice centre along that acquisition's normal (a tie goes
    to the lower slice), its signed offset from that slice's position is `(place - position) .
    normal`, and the slab rule names what that slab did with it, given the acquisition's own
    thickness, its pitch (`_pitch`, the same one the gap fraction uses) and whether the place falls
    inside THAT slice's in-plane rectangle [0, R-1] x [0, C-1]. The rule is applied to every place
    in ONE call of `knee.lenses.slab_kernels.slab_codes`, on the backend the request names: the
    reference applies the scalar `slab_code` per place and the twin is pinned SAME to it. The
    refusals -- a backend outside the registry, or one that cannot be built -- are raised by name
    and are not caught here.

    The in-plane test is made in the NEAREST slice's own frame (task 7.12): its origin is that
    slice's stored position, which is exact, and its basis is the selected plane's, which the
    stack shares under the precondition Chapter 1 measures and records as `orientation_spread`
    and `origin_spread_mm`. Until 7.12 every place was projected into the selected plane's frame,
    so one slice's origin stood for the whole stack, and a stack whose slice origins are displaced
    in-plane read a measured place as `outside_frame` and an outside place as `measured` (the
    Codex re-review's counterexample).

    None when the other acquisition's frame cannot place these places. A coordinate too large to
    hold is a non-finite offset, which the rule names `invalid_geometry`; it is no warning here.
    """
    normal, position, heights = stack
    if not np.all(np.isfinite(place_lps)):
        return None
    with np.errstate(all="ignore"):
        try:
            to_native = np.linalg.pinv(frame.basis_lps).T
        except (ValueError, TypeError, np.linalg.LinAlgError):
            return None
        order = np.argsort(heights, kind="stable")
        centres = heights[order]
        along = place_lps @ normal
        after = np.searchsorted(centres, along)
        below = np.clip(after - 1, 0, centres.size - 1)
        above = np.clip(after, 0, centres.size - 1)
        nearer = np.abs(along - centres[below]) <= np.abs(along - centres[above])
        nearest = order[np.where(nearer, below, above)]
        from_slice = place_lps - position[nearest]
        offset = from_slice @ normal
        native = from_slice @ to_native
        in_plane = (
            (native[:, 0] >= 0)
            & (native[:, 0] <= shape[0] - 1)
            & (native[:, 1] >= 0)
            & (native[:, 1] <= shape[1] - 1)
        )
        pitch = _pitch(centres, thickness)
        return slab_codes(offset, thickness, pitch, in_plane, backend)


def _slab_table(
    place_lps: np.ndarray | None,
    extent_of: np.ndarray,
    extents: int,
    series: object,
    measurement: object,
    backend: str,
) -> tuple[np.ndarray | None, str]:
    """What one OTHER acquisition's slabs did about every claimed place, or why it cannot say.

    Every source it needs is checked first and named when absent -- this plane's frame, the other
    acquisition's slice geometry, plane frame, plane and slice thickness -- so a bank is never
    written against a geometry that was not read. The counting is `count_by_extent` over the codes
    `_slab_codes` names.

    The array twin's refusals, `ValueError` for a backend outside the registry and `RuntimeError`
    for one that cannot be built, are caught here and nowhere else, and become the bank's reason by
    name. The stage stays total, and it never runs the reference in place of a refused backend.
    """
    if place_lps is None:
        return (
            None,
            "this plane's frame could not carry its places into the patient's frame",
        )
    stack = _stack(getattr(series, "geometry", None))
    if stack is None:
        return None, "the other acquisition's slice geometry was not read"
    frame = getattr(measurement, "frame", None)
    if not isinstance(frame, PlaneFrame):
        return None, "the other acquisition's plane frame was not read"
    plane = getattr(measurement, "acquired_plane", None)
    if not (isinstance(plane, np.ndarray) and plane.ndim == 2):
        return None, "the other acquisition's plane was not read"
    thickness = _finite(getattr(measurement, "slice_thickness_mm", None))
    if thickness is None:
        return None, "the other acquisition's slice thickness was not read"
    try:
        codes = _slab_codes(place_lps, stack, frame, plane.shape, thickness, backend)
    except (ValueError, RuntimeError) as error:
        return (
            None,
            f"{error}: the through-plane bank is not written against a backend the registry refused",
        )
    if codes is None:
        return None, "the other acquisition's frame could not place this plane's places"
    return count_by_extent(extent_of, codes, extents, len(SLAB_CODES)), ""


def _acquisitions(others: object) -> tuple[tuple[str, object, object], ...]:
    """Each other acquisition as (series uid, series, measurement), one entry per element handed over.

    An element that is not a (series, measurement) pair, or whose series names no uid, keeps a
    stable fallback name so that its bank still appears, unavailable, rather than vanishing.
    """
    if not isinstance(others, (tuple, list)):
        return ()
    found = []
    for index, pair in enumerate(others):
        readable = isinstance(pair, (tuple, list)) and len(pair) == 2
        series, measurement = pair if readable else (None, None)
        uid = getattr(getattr(series, "row", None), "series_uid", None)
        name = uid if isinstance(uid, str) and uid else f"unread_acquisition_{index}"
        found.append((name, series, measurement))
    return tuple(found)


def _through_plane_counts(
    claimed: np.ndarray,
    frame: object,
    extent_of: np.ndarray,
    extents: int,
    acquisitions: tuple[tuple[str, object, object], ...],
    backend: str,
) -> tuple[list[_Count], int]:
    """One through-plane bank per OTHER acquisition, in the order they were handed over.

    Also the counted work of those banks: the places the slab kernel evaluated, which is every
    claimed place for each acquisition whose bank was written and none for one that was carried
    unavailable, whatever the reason. A refused backend therefore adds nothing.
    """
    place_lps = _places_in_patient(frame, claimed) if acquisitions else None
    counts = []
    evaluated = 0
    for uid, series, measurement in acquisitions:
        table, why = _slab_table(
            place_lps, extent_of, extents, series, measurement, backend
        )
        if table is not None:
            evaluated += int(extent_of.size)
        counts.append(
            _Count(
                f"through_plane:{uid}",
                "study",
                SLAB_CODES,
                bank_status_code(table is not None, table is not None),
                table,
                f"counts of what acquisition {uid}'s slabs measured at this object's places, "
                "by the slab rule"
                if table is not None
                else why,
            )
        )
    return counts, evaluated


def _slab_gap(series: object, measurement: object) -> float | None:
    """One other acquisition's gap fraction from its own slice thickness and its pitch, or None.

    The pitch is `_pitch`'s, the one the through-plane bank uses, so the number and the bank can
    never disagree about the stack. None when the thickness or the slice geometry was not read;
    when either extent is not positive, because `gap_fraction` states `> 0` for both and the slab
    rule refuses such a geometry too, so a number here would contradict the bank; and when
    `gap_fraction` refuses the geometry. Its `ValueError` is a non-finite pitch, which an
    overflowing difference of huge heights can make. It reads nothing of this plane, of the other
    acquisition's frame or of its plane: the fraction is a property of its stack alone.
    """
    stack = _stack(getattr(series, "geometry", None))
    thickness = _finite(getattr(measurement, "slice_thickness_mm", None))
    if stack is None or thickness is None:
        return None
    with np.errstate(all="ignore"):
        pitch = _pitch(np.sort(stack[2]), thickness)
    if not (thickness > 0.0 and pitch > 0.0):
        return None
    try:
        return gap_fraction(thickness, pitch)
    except ValueError:
        return None


def _slab_gaps(
    acquisitions: tuple[tuple[str, object, object], ...],
) -> tuple[tuple[str, float | None], ...]:
    """The gap fraction of every OTHER acquisition, as (uid, fraction), in the order handed over."""
    return tuple(
        (uid, _slab_gap(series, measurement))
        for uid, series, measurement in acquisitions
    )


def _profiles(
    extent_labels: np.ndarray, places: np.ndarray, counts: list[_Count]
) -> tuple[ObjectProfile, ...]:
    """Slice every bank's table into one profile per extent, then carry the banks never written.

    Counts become plain Python ints here, once, and every profile gets its own row dicts.
    """
    tables = [None if count.table is None else count.table.tolist() for count in counts]
    profiles = []
    for index, (label, number) in enumerate(
        zip(extent_labels.tolist(), places.tolist(), strict=True)
    ):
        written = tuple(
            Bank(
                name=count.name,
                source_stage=count.source_stage,
                status=count.status,
                rows={}
                if table is None
                else dict(zip(count.names, table[index], strict=True)),
                why=count.why,
            )
            for count, table in zip(counts, tables, strict=True)
        )
        unavailable = tuple(
            Bank(
                name=name,
                source_stage="none",
                status=bank_status_code(False, False),
                rows={},
                why=why,
            )
            for name, why in UNAVAILABLE_BANKS
        )
        profiles.append(
            ObjectProfile(index=label, places=number, banks=written + unavailable)
        )
    return tuple(profiles)


def _write(
    ownership: object,
    lenses: object,
    measurements: object,
    acquisitions: tuple[tuple[str, object, object], ...],
    backend: str,
) -> tuple[BundlesReading, int, int]:
    """The reading, the lens-map places it read, and the places the slab kernel evaluated.

    The first count is the places of the lens maps read to write the reading. The second is the
    places the slab kernel evaluated, summed over every other acquisition whose bank was written.
    """
    standing = _ownership_standing(ownership)
    if standing != "present":
        code = stage_code(standing, True, True, 0)
        return _silence(code, _ownership_why(ownership, code), backend), 0, 0
    interiors = getattr(measurements, "interiors", None)
    labels = _labels(interiors)
    if labels is None:
        code = stage_code("present", interiors is not None, False, 0)
        why = _SUBJECT_WHY.get(code, "the extents cannot be read")
        return _silence(code, why, backend), 0, 0
    claimed = labels > 0
    extent_labels, extent_of = np.unique(labels[claimed], return_inverse=True)
    extents = int(extent_labels.size)
    code = stage_code("present", True, True, extents)
    if code != "present":
        why = _SUBJECT_WHY.get(code, "the extents cannot be read")
        return _silence(code, why, backend), 0, 0
    places = np.bincount(extent_of, minlength=extents)
    counts = _lens_counts(
        lenses, _plane_index(measurements), labels.shape, claimed, extent_of, extents
    )
    counts.append(_came_out(interiors, claimed, extent_labels, extent_of, extents))
    through_plane, slab_places = _through_plane_counts(
        claimed,
        getattr(measurements, "frame", None),
        extent_of,
        extents,
        acquisitions,
        backend,
    )
    counts.extend(through_plane)
    lens_read = any(
        c.source_stage == "lenses" and c.status == "written" for c in counts
    )
    reading = BundlesReading(
        code="present",
        why=(
            f"{extents} indexed extents of the selected native plane, keyed on the interiors' "
            f"labels (the solitary parse); ownership seated: {_seated(ownership)}"
        ),
        subject_kind=SUBJECT_KIND,
        planes_read=1,
        profiles=_profiles(extent_labels, places, counts),
        backend=backend,
        slab_gaps=_slab_gaps(acquisitions),
    )
    return reading, (int(places.sum()) if lens_read else 0), slab_places


def read_bundles(
    ownership: object,
    lenses: object,
    measurements: object,
    others: tuple[object, ...] = (),
    backend: str = "reference",
) -> BundlesReading:
    """Write every object's profile, or name the silence met instead.

    TOTAL over its arguments and it never raises. A profile is keyed on one indexed extent of the
    selected native plane, read as `measurements.interiors.labels == k` for every k > 0; ownership
    is read for its code and its seating only, and when it is not `present` the stage returns
    ownership's own code with no profile. Each bank counts the one quantity it names, and a bank
    whose source is absent is carried `unavailable` with the reason, never as rows of zero.

    `backend` names the kernel the through-plane banks use for the slab rule, "reference" or "jit",
    and is recorded on the reading as requested. A backend the registry refuses makes those banks
    unavailable with the refusal by name; the stage neither raises nor runs the reference in its
    place, and the banks that need no kernel are unaffected.

    The reading also carries `slab_gaps`: one gap fraction per other acquisition, read from that
    acquisition's own stack alone, so it does not depend on the backend or on this plane's frame.

    `vectors.produced` is recorded on every path: the route reaches this stage unconditionally
    and a silent stage must still say what it produced. It carries the counted work of the
    through-plane banks, `slab_places`: the places the slab kernel evaluated. A consumption is
    recorded only for a record handed over (`specs/route-composition`, task 7.14): a None
    predecessor was not produced, and the reading's own code names that silence.
    """
    acquisitions = _acquisitions(others)
    reading, places, slab_places = _write(
        ownership, lenses, measurements, acquisitions, backend
    )
    if ownership is not None:
        ledger.record("ownership.consumed_by.vectors", readings=1)
    if lenses is not None:
        ledger.record("lenses.consumed_by.vectors", readings=1, places=places)
    if measurements is not None:
        ledger.record("objects.consumed_by.vectors", readings=1)
    ledger.record("study.consumed_by.vectors", acquisitions=len(acquisitions))
    ledger.record(
        "vectors.produced", profiles=len(reading.profiles), slab_places=slab_places
    )
    return reading
