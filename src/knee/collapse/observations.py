"""What each view says of one anatomical object, kept by where the saying comes from.

**Why it exists.** "No view is the truth alone, and what an <object> is, is what the views recover
together" (*What an <Object> Is* §1.3), and an object found in one view of the leg is that object in
every other view of it (`docs/THEORY_OF_THE_CASE.md` Law 9). The run already keeps each part's
masks and decisions per slice; this adds the one index that says, for one object, which of those
records are readings of it and how each one knows it: `docs/DIMENSIONAL_COLLAPSE_PLAN.md` Step 1.
It derives from the records and masks the run already makes (`scripts/run_interiors.py`
assembles it from them) and holds no pixels of its own: the places an observation rests on are
the arrays of the record it points to.

**The provenances, never collapsed.**

- `native`: the part was identified on this slice by its own rule (`resolved`), or a cheap
  reading on the slice measured its body (`reading`: a pointer or a continuation, no boundary
  claimed). An axial series' own lens territory holding most of the part's physical places that lie
  within one of its slabs is also a native `reading` (a territory under the places, not a
  boundary); the places off every slab are not projected for it.
- `laid`: the part, resolved on the same place in the other sequence, laid onto this slice by the
  pair's one match of places (Rohan, 2026-10-14: «It's literally the same leg, obviously the object
  would be the same in both views»). It is an observation with its own provenance, and the places
  the match cannot map are left out of it.
- `projected`: the part's places in the scanner's millimetres projected onto a slice of another
  plane, however far off it they lie. It is a `target`: where a native question about the part
  may be asked there, never a boundary segmented on that slice. A target is therefore never
  `resolved`, and a resolved observation is never a target: the types refuse the combination.

**Where the places are kept** (`artifact`, `row`, `label`). An observation holds no pixels; the
array it names is in the saved artifact of one record, the file `save` made for it, named exactly as
the receipt names it (`record["artifact"]`: the study's folder and `<series uid>-<part>.npz` for a
part's own slice). `artifact` is that path, which is the containing record's anchor (its series,
part and native slice index are on the record the receipt keeps under it); `support` is the array
in it. Which part of the array: for an array with one entry per native slice (a profile), the
`slices` of the observation are its first-axis indices; for a stack of planes, `row` is the
observation's index along its first axis; for a labelled array, `label` is the value that selects
its places (`a1_objects == label`). A label selects only in an integer-coded array: a boolean mask
has none (its places are the mask), and the number of a lens territory belongs to the labelled
array beside it, never to the mask. For a flat PACKED array (planes or traces of unequal size
written end to end), `row` indexes the offsets the record keeps for it, and the observation's
`note` states the slice it is: `offsets[row]:offsets[row + 1]` of the support, reshaped by the
`shapes` kept beside the offsets for planes (`a3_fibula_axial_*`), or the points of a trace
(`a3_posterior_trace_<object>_*`). A native, a laid and a projected observation therefore name
different artifacts and cannot be mistaken for one another. What no stage could place is not
dropped: it is an `Unresolved` with its code, per provenance, and is never an absence.

An unseen or unmeasured value is None, never 0.
"""

from __future__ import annotations

import math
from dataclasses import asdict, dataclass

PROVENANCES = ("native", "laid", "projected")
KINDS = ("resolved", "reading", "target")


@dataclass(frozen=True, slots=True)
class Observation:
    """One view's saying of one object: `object` the part's name; `provenance` and `kind` as above;
    `series_uid` and `view` (plane, fluid-sensitive, fat-suppressed) the series it lies in;
    `slices` its native slice indices (a reading may span several, a resolved observation or a
    target has one); `code` the decision or the placing on that slice; `count` how many places
    (pixels) it rests on there, None where none were counted; `off_plane_mm` how far the object's
    places lie from the slice's plane (0.0 for an observation made on the slice, None where it is
    not known); `support` which array of its record holds its places, or how they are recovered;
    `note` what it does not say; `artifact`, `row` and `label` where the support's places are (above),
    None where an observation names no array."""

    object: str
    provenance: str
    kind: str
    series_uid: str
    view: tuple[str, str, str]
    slices: tuple[int, ...]
    code: str
    count: int | None
    off_plane_mm: float | None
    support: str
    note: str
    artifact: str | None = None
    row: int | None = None
    label: int | None = None

    def __post_init__(self) -> None:
        if self.provenance not in PROVENANCES:
            raise ValueError("unknown_provenance")
        if self.kind not in KINDS:
            raise ValueError("unknown_kind")
        if (self.provenance == "projected") != (self.kind == "target"):
            # a projected place is only a target; only a projected place is one
            raise ValueError("a_target_is_projected_and_a_projection_is_only_a_target")
        if self.kind == "resolved" and self.provenance not in ("native", "laid"):
            raise ValueError("resolved_is_native_or_laid")
        if not self.slices:
            raise ValueError("an_observation_lies_on_a_slice")
        if self.kind != "reading" and len(self.slices) != 1:
            raise ValueError("a_resolved_observation_or_target_has_one_slice")
        if self.off_plane_mm is not None and not (
            math.isfinite(self.off_plane_mm) and self.off_plane_mm >= 0
        ):
            raise ValueError("off_plane_distance_is_a_finite_length_or_unknown")
        if self.row is not None and self.row < 0:
            raise ValueError("a_row_is_an_index_into_the_support")
        if self.row is not None and self.artifact is None:
            raise ValueError("a_row_is_in_an_artifact")
        if self.label is not None and self.artifact is None:
            raise ValueError("a_label_selects_in_an_artifact")


@dataclass(frozen=True, slots=True)
class Unresolved:
    """A saying of one object that could not be made, kept by what it is the lack of: `provenance`
    ("laid", "projected", or "native" for a reading asked of an axial series' own territories),
    the `series_uid` and `view` it was asked of (None where there is no such series, as where the
    study has no other sequence or no axial one), and the `code` that names why: a failed
    transfer's own result or the missing geometry fact. It is an unknown, never an absence of the
    object, and no boundary is fabricated for it."""

    object: str
    provenance: str
    series_uid: str | None
    view: tuple[str, str, str] | None
    code: str

    def __post_init__(self) -> None:
        if self.provenance not in PROVENANCES:
            raise ValueError("only_a_transfer_or_a_projection_can_be_unresolved")
        if not self.code:
            raise ValueError("an_unresolved_saying_names_why")


def rows(observations: list[Observation]) -> list[dict]:
    """The observations as plain records for a receipt, each tuple a list."""
    return [asdict(observation) for observation in observations]


def unresolved_rows(unresolved: list[Unresolved]) -> list[dict]:
    """The unresolved sayings as plain records for a receipt."""
    return [asdict(item) for item in unresolved]


def tally(observations: list[Observation]) -> dict[str, int]:
    """How many observations each provenance holds, every provenance named, none left out."""
    counts = dict.fromkeys(PROVENANCES, 0)
    for observation in observations:
        counts[observation.provenance] += 1
    return counts


REFERENCE_KEYS = (
    "series_uid",
    "view",
    "slices",
    "code",
    "count",
    "off_plane_mm",
    "support",
    "artifact",
    "row",
    "label",
)


def describe_objects(records: list[dict]) -> dict[str, dict]:
    """The study's anatomical objects, each described by every observation the records keep of it:
    the one coherent output of the operation, grouped by object, then provenance, then kind, then
    property (`support`: the array that holds the places, which says what the places measure).

    It adds no pixels and no judgement. Each entry is a reference (`REFERENCE_KEYS`: the series,
    its slices, the decision, how many places, where the places are: artifact, row, label) to
    arrays already saved. For every object it also keeps `outcomes`, how often each named code
    came, and its `unresolved` sayings by provenance and code, so a part not read, ambiguous, tied
    or unavailable is never mistaken for one found absent, and `native_series`, the series that
    resolved it on a slice of their own. A projected target stays under `projected`/`target`: a
    place to ask, never a boundary. Records without observations contribute nothing."""
    described: dict[str, dict] = {}

    def entry(name: str) -> dict:
        return described.setdefault(
            name,
            {
                "observations": {},
                "outcomes": {},
                "unresolved": {},
                "native_series": [],
            },
        )

    for record in records:
        for row in record.get("observations", []):
            got = entry(row["object"])
            by_kind = got["observations"].setdefault(row["provenance"], {})
            by_property = by_kind.setdefault(row["kind"], {})
            by_property.setdefault(row["support"], []).append(
                {key: row[key] for key in REFERENCE_KEYS}
            )
            got["outcomes"][row["code"]] = got["outcomes"].get(row["code"], 0) + 1
            if (
                row["provenance"] == "native"
                and row["kind"] == "resolved"
                and row["series_uid"] not in got["native_series"]
            ):
                got["native_series"].append(row["series_uid"])
        for row in record.get("observations_unresolved", []):
            by_code = entry(row["object"])["unresolved"].setdefault(
                row["provenance"], {}
            )
            by_code[row["code"]] = by_code.get(row["code"], 0) + 1
    return dict(sorted(described.items()))
