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

from knee.collapse.anatomical_relations import relationships_for

PROVENANCES = ("native", "laid", "projected")
KINDS = ("resolved", "reading", "target")


def address_frame_status(frame: dict) -> str:
    """Return the named validity of a retained observation address frame."""
    if not isinstance(frame, dict):
        return "frame_invalid"
    origin, basis = frame.get("origin_lps"), frame.get("basis_lps")
    if (
        not isinstance(origin, (list, tuple))
        or len(origin) != 3
        or not isinstance(basis, (list, tuple))
        or len(basis) != 3
        or any(not isinstance(row, (list, tuple)) or len(row) != 2 for row in basis)
    ):
        return "frame_invalid"
    values = (*origin, *(component for row in basis for component in row))
    if any(
        isinstance(value, bool) or not isinstance(value, (int, float))
        for value in values
    ):
        return "frame_invalid"
    try:
        numeric = tuple(float(value) for value in values)
    except OverflowError:
        return "frame_invalid"
    if not all(math.isfinite(value) for value in numeric):
        return "frame_invalid"
    a = [float(row[0]) for row in basis]
    b = [float(row[1]) for row in basis]
    scale_a, scale_b = max(map(abs, a)), max(map(abs, b))
    # Only an exactly zero basis vector is invalid; tiny nonzero scales remain valid.
    if scale_a == 0.0 or scale_b == 0.0:  # NOSONAR(S1244)
        return "frame_invalid"
    a = [value / scale_a for value in a]
    b = [value / scale_b for value in b]
    cross = (
        a[1] * b[2] - a[2] * b[1],
        a[2] * b[0] - a[0] * b[2],
        a[0] * b[1] - a[1] * b[0],
    )
    # Reject exact collinearity, not a tolerance-defined small but nonzero plane.
    if not any(value != 0.0 for value in cross):  # NOSONAR(S1244)
        return "frame_invalid"
    return "frame_valid"


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
    address_frame: dict[str, object] | None = None

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
        if self.address_frame is not None:
            origin = self.address_frame.get("origin_lps")
            basis = self.address_frame.get("basis_lps")
            if (
                not isinstance(origin, (list, tuple))
                or len(origin) != 3
                or not isinstance(basis, (list, tuple))
                or len(basis) != 3
                or any(
                    not isinstance(row, (list, tuple)) or len(row) != 2 for row in basis
                )
                or any(
                    isinstance(value, bool)
                    or not isinstance(value, (int, float))
                    or not math.isfinite(value)
                    for value in (*origin, *(value for row in basis for value in row))
                )
            ):
                raise ValueError(
                    "observation_address_frame_is_finite_lps_origin_and_3x2_basis"
                )
            if len(self.slices) != 1:
                raise ValueError("one_address_frame_names_one_native_slice")


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
    result = [asdict(observation) for observation in observations]
    for row in result:
        if row.get("address_frame") is None:
            row.pop("address_frame")
    return result


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


MARROW_SCOPE_NOTE = (
    "associated native calibration/profile references only; no independent "
    "full-resolution marrow segmentation or volume"
)

MARROW_MEANING = (
    "median acquired light over the named whole-bone support "
    "(native middle a1_objects == OBJECT_CODES[bone]); not a marrow-only reference"
)

MARROW_NATIVE = "native_calibration_and_profile_reading"

MARROW_UNRESOLVED = "native_reader_unresolved"

MARROW_UNAVAILABLE = "native_marrow_measurement_unavailable"

NOT_RETAINED = "not_retained_in_receipt"


def _array_reference(record: dict, name: str) -> dict | None:
    """A saved array's receipt reference: the digest is all the record retains."""
    saved = record.get("arrays", {}).get(name)
    artifact = record.get("artifact")
    if (
        not isinstance(artifact, str)
        or not artifact
        or not isinstance(saved, dict)
        or not isinstance(saved.get("digest"), str)
    ):
        return None
    return {
        "artifact": record.get("artifact"),
        "name": name,
        "digest": saved["digest"],
        "dtype_shape": NOT_RETAINED,
    }


def _valid_calibration(value: object) -> bool:
    return (
        isinstance(value, (int, float))
        and not isinstance(value, bool)
        and math.isfinite(value)
        and value > 0
    )


def _marrow_series(record: dict, bone: str) -> dict | None:
    """One series' associated marrow reading of one bone, from its saved record only."""
    from knee.objects.assignments import OBJECT_CODES

    bones = record.get("bones")
    if not isinstance(bones, dict):
        return None
    codes = bones.get("codes")
    code = codes.get(bone) if isinstance(codes, dict) else None
    read = bones.get(bone)
    basis_ok = isinstance(read, dict)
    if isinstance(read, dict) and code is None:
        code = read.get("outcome")
    light = read.get("marrow_light") if isinstance(read, dict) else None
    prefixes = (f"a3_{bone}_profile_", f"a3_{bone}_fine_")
    profile = [
        ref
        for name in sorted(record.get("arrays", {}))
        if name.startswith(prefixes)
        and (ref := _array_reference(record, name)) is not None
    ]
    calibration_ref = _array_reference(record, f"a3_{bone}_reference_light")
    objects_ref = _array_reference(record, "a1_objects")
    ready = (
        basis_ok
        and code != "unreadable"
        and _valid_calibration(light)
        and calibration_ref is not None
        and objects_ref is not None
        and bool(profile)
    )
    availability = (
        MARROW_NATIVE
        if ready
        else MARROW_UNRESOLVED
        if code == "unreadable" or (basis_ok and not _valid_calibration(light))
        else MARROW_UNAVAILABLE
    )
    return {
        "study_uid": record.get("study_uid"),
        "series_uid": record.get("series_uid"),
        "view": record.get("view"),
        "slice_index": record.get("slice_index"),
        "artifact": record.get("artifact"),
        "reader_outcome": code,
        "basis_refusal_code": code if not basis_ok and isinstance(code, str) else None,
        "availability": availability,
        "calibration": {
            "marrow_light": light,
            "reference": calibration_ref,
            "support": {
                "reference": objects_ref if basis_ok else None,
                "label": OBJECT_CODES[bone] if basis_ok else None,
                "slice_index": record.get("slice_index"),
                "meaning": MARROW_MEANING,
            },
        },
        "profile_references": profile,
    }


def _marrow_field(name: str, records: list[dict]) -> dict | None:
    """The associated marrow reading of one bone entry, or None for a non-bone object."""
    series: list[dict] = []
    if name in ("femur", "tibia"):
        series = [s for r in records if (s := _marrow_series(r, name)) is not None]
        native = any(s["availability"] == MARROW_NATIVE for s in series)
        availability = (
            MARROW_NATIVE
            if native
            else MARROW_UNRESOLVED
            if any(s["availability"] == MARROW_UNRESOLVED for s in series)
            else MARROW_UNAVAILABLE
        )
        meaning = MARROW_MEANING
    elif name in ("patella", "fibula"):
        availability, meaning = MARROW_UNAVAILABLE, None
    else:
        return None
    return {
        "kind": "reading",
        "availability": availability,
        "measurement": meaning,
        "scope_note": MARROW_SCOPE_NOTE,
        "unavailability_reason": (
            "not_linked_by_current_native_marrow_reader"
            if name in ("patella", "fibula")
            else None
        ),
        "series": series,
    }


def describe_objects(
    records: list[dict],
    objects: tuple[str, ...] = (),
    silences: dict[str, str] | None = None,
) -> dict[str, dict]:
    """The study's anatomical objects, each described by every observation the records keep of it:
    the one coherent output of the operation, grouped by object, then provenance, then kind, then
    property (`support`: the array that holds the places, which says what the places measure).

    `anatomical_relations` supplies sourced, typed definition links to other entries in this
    same object table. Their basis is anatomical definition, not a claim that this study
    measured each attachment or enclosure; native evidence and unresolved readings stay separate.

    It adds no pixels and no judgement. Each entry is a reference (`REFERENCE_KEYS`: the series,
    its slices, the decision, how many places, where the places are: artifact, row, label) to
    arrays already saved. For every object it also keeps `outcomes`, how often each named code
    came, and its `unresolved` sayings by provenance and code, so a part not read, ambiguous, tied
    or unavailable is never mistaken for one found absent, and `native_series`, the series that
    resolved it on a slice of their own. `definition_decisions` retains every categorical
    assignment record for the exact object, including named and abstaining codes, while
    `search_refusals` retains that object's own-slice silences. These categorical records remain
    available as new observations arrive. A projected target stays under `projected`/`target`: a
    place to ask, never a boundary. `objects` declares the production catalogue: a feature with
    neither an observation nor a recorded refusal keeps `no_observation_record`, never absence.
    `silences` supplies the driver\'s existing `<series uid>:<part>` own-slice refusals; for an
    otherwise unrepresented feature those and its retained definition abstentions supply the
    specific reason, without creating a new image observation or changing any measurement."""
    described: dict[str, dict] = {}

    def entry(name: str) -> dict:
        return described.setdefault(
            name,
            {
                "observations": {},
                "outcomes": {},
                "unresolved": {},
                "native_series": [],
                "definition_decisions": [],
                "search_refusals": [],
            },
        )

    for name in objects:
        entry(name)

    for record in records:
        for row in record.get("observations", []):
            got = entry(row["object"])
            by_kind = got["observations"].setdefault(row["provenance"], {})
            by_property = by_kind.setdefault(row["kind"], {})
            reference = {key: row[key] for key in REFERENCE_KEYS}
            if row.get("address_frame") is not None:
                reference["address_frame"] = row["address_frame"]
            if row.get("support_address_kind") is not None:
                reference["support_address_kind"] = row["support_address_kind"]
            by_property.setdefault(row["support"], []).append(reference)
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
    # Collect the retained categorical records once, shared by every object entry.
    for record in records:
        for name, code in record.get("assignments", {}).get("codes", {}).items():
            if name in described and isinstance(code, str):
                described[name]["definition_decisions"].append(
                    {
                        "series_uid": record.get("series_uid"),
                        "view": record.get("view"),
                        "slice_index": record.get("slice_index"),
                        "artifact": record.get("artifact"),
                        "main_object": record.get("main_slice", {}).get("object"),
                        "code": code,
                    }
                )
    for key, code in sorted((silences or {}).items()):
        uid, separator, part = key.rpartition(":")
        if separator and part in described:
            described[part]["search_refusals"].append({"series_uid": uid, "code": code})
    for name, got in described.items():
        if got["observations"] or got["unresolved"]:
            continue
        # A specific refusal already retained by a definition or its own-slice search is more
        # informative than the generic missing-observation marker. Do not reinterpret successful
        # naming codes, generic not-named markers, or another object\'s refusal as this object\'s.
        refused = {
            (str(record.get("series_uid", "")), code)
            for record in records
            if isinstance(
                (code := record.get("assignments", {}).get("codes", {}).get(name)), str
            )
            and code.startswith("abstain_")
        }
        for key, code in (silences or {}).items():
            uid, separator, part = key.rpartition(":")
            if separator and part == name:
                refused.add((uid, code))
        if refused:
            counts: dict[str, int] = {}
            for _, code in sorted(refused):
                counts[code] = counts.get(code, 0) + 1
            got["unresolved"] = {"native": counts}
        else:
            got["unresolved"] = {"pipeline": {"no_observation_record": 1}}
    # Definitions link the same object entries without declaring that this study measured
    # an attachment or enclosure. Actual observations and refusals remain their own evidence.
    for name, relations in relationships_for(tuple(described)).items():
        described[name]["anatomical_relations"] = relations
    for name, got in described.items():
        field = _marrow_field(name, records)
        if field is not None:
            got["associated_fields"] = {"marrow": field}
    return dict(sorted(described.items()))
