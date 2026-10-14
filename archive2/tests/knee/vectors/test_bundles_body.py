"""The bundles body, both signs (task 6.7): what each bank counts, from fields the stages below made.

Written by the lead BEFORE the body, from `specs/object-bundles/spec.md` and the banks declared in
`knee.vectors.bundles`. Every expectation below is computed from the predecessor records directly,
so the body is checked against the stages it reads and never against itself.

Row vocabularies: `own_reading:<member>` rows are `DIGIT_CODES`; `lens_standing` rows are
`STANDING_CODES`; `came_out` rows are `edge_kind:<name>` over `EDGE_KINDS` and `trace:<name>` over
`TRACE_CODES`; `through_plane:<uid>` rows are `SLAB_CODES`. Every bank is keyed on the indexed
extent of the selected plane, read off `interiors.labels`.
"""

from types import SimpleNamespace

import numpy as np
import pytest

from knee.absence import CODES as ABSENCE_CODES
from knee.collapse.physical import PlaneFrame
from knee.lenses.digits import DIGIT_CODES
from knee.lenses.members import STANDING_CODES
from knee.lenses.places import MEMBERS, read_lenses
from knee.lenses.slabs import SLAB_CODES, gap_fraction
from knee.objects.interiors import EDGE_KINDS, TRACE_CODES, read_interiors
from knee.ownership.claims import read_ownership_members
from knee.study.series import SeriesGeometry
from knee.telemetry import recording
from knee.vectors.bundles import SUBJECT_KIND, UNAVAILABLE_BANKS, read_bundles

OFFSETS = np.array([-2.0, -1.0, 0.0, 1.0, 2.0])
AXIAL = np.array([1.0, 0.0, 0.0, 0.0, 1.0, 0.0])
BOTH = SimpleNamespace(
    terciles=(50.0, 150.0),
    foreground_count=8,
    tercile_minimum_population=8,
    split_terciles=(0.5, 50.0),
    split_population_count=8,
)
FIRST_ONLY = SimpleNamespace(
    terciles=(50.0, 150.0), foreground_count=8, tercile_minimum_population=8
)


def _plane() -> np.ndarray:
    """Two bright bodies with a dark band between them."""
    plane = np.full((24, 24), 100.0)
    plane[10:14, :] = 1.0
    return plane


def _frame(z: float = 0.0) -> PlaneFrame:
    return PlaneFrame.from_dicom(np.array([0.0, 0.0, z]), AXIAL, np.array([1.0, 1.0]))


def _interiors(plane: np.ndarray):
    return read_interiors(plane, (1.0, 1.0), 10.0, 1.0, OFFSETS)


def _measurement(plane, interiors, z: float = 0.0, thickness: float = 3.0):
    return SimpleNamespace(
        code="measured",
        slice_index=0,
        frame=_frame(z),
        acquired_plane=plane,
        interiors=interiors,
        slice_thickness_mm=thickness,
    )


def _other(uid: str, heights, thickness: float = 3.0, shape=(24, 24)):
    """Another acquisition of the same orientation, its slabs at the given heights."""
    heights = [float(h) for h in heights]
    positions = np.array([[0.0, 0.0, z] for z in heights])
    geometry = SeriesGeometry(
        normal=np.array([0.0, 0.0, 1.0]),
        orientation=np.tile(AXIAL, (len(heights), 1)),
        position=positions,
        spacing=np.tile([1.0, 1.0], (len(heights), 1)),
        along_normal=np.array(heights),
        orientation_spread=0.0,
    )
    series = SimpleNamespace(
        row=SimpleNamespace(series_uid=uid),
        geometry=geometry,
        volume=np.zeros((len(heights), *shape)),
    )
    measurement = SimpleNamespace(
        code="measured",
        slice_index=0,
        frame=_frame(heights[0]),
        acquired_plane=np.zeros(shape),
        interiors=None,
        slice_thickness_mm=thickness,
    )
    return series, measurement


def _bundle(
    plane=None, key=BOTH, others=(), z: float = 0.0, backend: str = "reference"
):
    plane = _plane() if plane is None else plane
    interiors = _interiors(plane)
    ownership = read_ownership_members(interiors, None)
    lenses = read_lenses(plane[None], key)
    reading = read_bundles(
        ownership, lenses, _measurement(plane, interiors, z), others, backend=backend
    )
    return reading, interiors, lenses


def _bank(profile, name):
    banks = {bank.name: bank for bank in profile.banks}
    assert name in banks, f"{name} missing from {sorted(banks)}"
    return banks[name]


# ---------------------------------------------------------------- positive


def test_one_profile_per_object_keyed_on_the_indexed_extent() -> None:
    reading, interiors, _ = _bundle()
    labels = interiors.labels
    expected = {int(k): int((labels == k).sum()) for k in np.unique(labels[labels > 0])}
    assert len(expected) >= 2
    assert reading.code == "present"
    assert reading.subject_kind == SUBJECT_KIND
    assert reading.planes_read == 1
    assert {p.index: p.places for p in reading.profiles} == expected


def test_own_reading_banks_count_the_lens_codes_at_the_objects_places() -> None:
    reading, interiors, lenses = _bundle()
    for profile in reading.profiles:
        inside = interiors.labels == profile.index
        for member in lenses.members:
            bank = _bank(profile, f"own_reading:{member.population}")
            assert bank.status == "written"
            assert bank.source_stage == "lenses"
            assert tuple(bank.rows) == DIGIT_CODES
            counts = np.bincount(member.codes[0][inside], minlength=len(DIGIT_CODES))
            assert [bank.rows[name] for name in DIGIT_CODES] == counts.tolist()
            assert sum(bank.rows.values()) == profile.places


def test_the_standing_bank_counts_what_the_members_jointly_said() -> None:
    reading, interiors, lenses = _bundle()
    for profile in reading.profiles:
        inside = interiors.labels == profile.index
        bank = _bank(profile, "lens_standing")
        assert tuple(bank.rows) == STANDING_CODES
        counts = np.bincount(lenses.standings[0][inside], minlength=len(STANDING_CODES))
        assert [bank.rows[name] for name in STANDING_CODES] == counts.tolist()


def test_came_out_bank_counts_the_objects_edge_kinds_and_trace_codes() -> None:
    reading, interiors, _ = _bundle()
    for profile in reading.profiles:
        bank = _bank(profile, "came_out")
        assert bank.source_stage == "objects"
        assert bank.status == "written"
        mine = interiors.edge_regions == profile.index
        for name, value in EDGE_KINDS.items():
            assert bank.rows[f"edge_kind:{name}"] == int(
                (mine & (interiors.edge_kinds == value)).sum()
            )
        for name, value in TRACE_CODES.items():
            assert bank.rows[f"trace:{name}"] == int(
                (mine & (interiors.trace_codes == value)).sum()
            )
        assert set(bank.rows) == (
            {f"edge_kind:{n}" for n in EDGE_KINDS}
            | {f"trace:{n}" for n in TRACE_CODES}
            | {"seeds"}
        )


def test_came_out_bank_counts_the_objects_seeds() -> None:
    """Task 3.2: how the object came out includes its seeds, the prominence-marker places the
    objects stage grew it from, counted inside the extent and from the markers field only."""
    reading, interiors, _ = _bundle()
    assert interiors.markers.shape == interiors.labels.shape
    for profile in reading.profiles:
        bank = _bank(profile, "came_out")
        inside = interiors.labels == profile.index
        assert bank.rows["seeds"] == int((inside & (interiors.markers != 0)).sum())
    assert sum(_bank(p, "came_out").rows["seeds"] for p in reading.profiles) >= 2


def test_came_out_is_unavailable_when_the_markers_do_not_read_as_this_field() -> None:
    """MUST NOT: count seeds from a markers field of another shape, or write the bank without them."""
    plane = _plane()
    interiors = _interiors(plane)
    ownership = read_ownership_members(interiors, None)
    broken = SimpleNamespace(
        **{
            name: getattr(interiors, name)
            for name in ("labels", "edge_regions", "edge_kinds", "trace_codes")
        },
        markers=np.zeros((2, 2), dtype=np.int32),
    )
    measurement = SimpleNamespace(
        code="measured",
        slice_index=0,
        frame=_frame(),
        acquired_plane=plane,
        interiors=broken,
        slice_thickness_mm=3.0,
    )
    reading = read_bundles(ownership, read_lenses(plane[None], BOTH), measurement, ())
    assert reading.code == "present"
    for profile in reading.profiles:
        bank = _bank(profile, "came_out")
        assert bank.status == "unavailable"
        assert dict(bank.rows) == {}
        assert "markers" in bank.why


def test_through_plane_bank_consumes_the_slab_rule_for_every_other_acquisition() -> (
    None
):
    # The other acquisition has slabs 3 mm thick centred at 0 and 10 mm; this plane sits at 0,
    # so every place of every object lies inside its first slab: measured, and nothing else.
    reading, _, _ = _bundle(others=(_other("B", [0.0, 10.0]),))
    for profile in reading.profiles:
        bank = _bank(profile, "through_plane:B")
        assert bank.status == "written"
        assert tuple(bank.rows) == SLAB_CODES
        assert bank.rows["measured"] == profile.places
        assert sum(bank.rows.values()) == profile.places


def test_a_plane_between_two_slabs_is_in_the_gap_of_that_acquisition() -> None:
    # The same other acquisition, but this plane sits at 5 mm: 3.5 mm beyond either slab's
    # half-thickness and exactly at half the 10 mm pitch, so every place falls in the gap.
    reading, _, _ = _bundle(others=(_other("B", [0.0, 10.0]),), z=5.0)
    for profile in reading.profiles:
        bank = _bank(profile, "through_plane:B")
        assert bank.rows["in_gap"] == profile.places


def test_a_place_outside_the_other_acquisitions_frame_is_outside_frame() -> None:
    # A 4x4 other acquisition covers only the first four rows and columns of this plane.
    reading, interiors, _ = _bundle(others=(_other("B", [0.0, 10.0], shape=(4, 4)),))
    for profile in reading.profiles:
        bank = _bank(profile, "through_plane:B")
        rows, cols = np.nonzero(interiors.labels == profile.index)
        inside = int(((rows <= 3) & (cols <= 3)).sum())
        assert bank.rows["measured"] == inside
        assert bank.rows["outside_frame"] == profile.places - inside


def test_the_in_plane_test_is_made_in_the_nearest_slices_own_frame() -> None:
    """MUST NOT (task 7.12): apply one slice's in-plane origin to the whole stack. The other
    acquisition's second slice is displaced 20 mm along the column direction; this plane sits at
    its height, so that slab is the nearest for every place, and a place is inside its frame only
    where its column is 20 or more. The shared-frame shortcut read every place as measured, which
    is the Codex re-review's counterexample: a measured place as `outside_frame`, an outside
    place as `measured`, by one slice's rectangle standing for another's."""
    geometry = SeriesGeometry(
        normal=np.array([0.0, 0.0, 1.0]),
        orientation=np.tile(AXIAL, (2, 1)),
        position=np.array([[0.0, 0.0, 0.0], [20.0, 0.0, 10.0]]),
        spacing=np.tile([1.0, 1.0], (2, 1)),
        along_normal=np.array([0.0, 10.0]),
        orientation_spread=0.0,
    )
    series = SimpleNamespace(
        row=SimpleNamespace(series_uid="B"),
        geometry=geometry,
        volume=np.zeros((2, 24, 24)),
    )
    measurement = SimpleNamespace(
        code="measured",
        slice_index=0,
        frame=_frame(0.0),
        acquired_plane=np.zeros((24, 24)),
        interiors=None,
        slice_thickness_mm=3.0,
    )
    reading, interiors, _ = _bundle(others=((series, measurement),), z=10.0)
    for profile in reading.profiles:
        bank = _bank(profile, "through_plane:B")
        assert bank.status == "written"
        _rows, cols = np.nonzero(interiors.labels == profile.index)
        inside = int((cols >= 20).sum())
        assert bank.rows["measured"] == inside
        assert bank.rows["outside_frame"] == profile.places - inside
        assert bank.rows["in_gap"] == bank.rows["not_this_slice"] == 0


def test_the_reading_carries_each_other_acquisitions_gap_fraction() -> None:
    """Task 7.2: `gap_fraction` is a property of the ACQUISITION that "belongs beside a
    conjunction as the prior probability that a foreign place falls into nothing" (its own
    docstring), so the stage records it per other acquisition from that acquisition's thickness
    and pitch, and None where either was not read. The slab rule's second consumer."""
    others = (
        _other("B", [0.0, 10.0], thickness=3.0),
        _other("C", [0.0, 2.0, 4.0], thickness=4.0),
    )
    reading, _, _ = _bundle(others=others)
    assert dict(reading.slab_gaps) == {"B": gap_fraction(3.0, 10.0), "C": 0.0}
    series = SimpleNamespace(
        row=SimpleNamespace(series_uid="D"), geometry=None, volume=None
    )
    measurement = SimpleNamespace(
        code="no_stacked_volume",
        slice_index=None,
        frame=None,
        interiors=None,
        acquired_plane=None,
        slice_thickness_mm=None,
    )
    reading, _, _ = _bundle(others=((series, measurement),))
    assert dict(reading.slab_gaps) == {"D": None}


def test_unavailable_banks_are_carried_by_name_with_their_reason_and_no_rows() -> None:
    reading, _, _ = _bundle()
    for profile in reading.profiles:
        for name, why in UNAVAILABLE_BANKS:
            bank = _bank(profile, name)
            assert bank.status == "unavailable"
            assert bank.why == why
            assert dict(bank.rows) == {}


def test_a_silent_member_writes_its_silence_rows_never_a_digit() -> None:
    # The second member has no population, so every one of its places is a named silence.
    reading, _, lenses = _bundle(key=FIRST_ONLY)
    silent = lenses.members[1]
    assert silent.code != "present"
    for profile in reading.profiles:
        bank = _bank(profile, f"own_reading:{silent.population}")
        assert bank.rows["below"] == bank.rows["at"] == bank.rows["above"] == 0
        assert sum(bank.rows.values()) == profile.places


def test_the_ledger_records_what_the_stage_read_and_wrote() -> None:
    """Tasks 6.5 and 7.14: each consumption under its own name with the readings handed over, the
    lens-map places read and the acquisitions; the stage's production on every path; and NO
    consumption of a predecessor handed over as None, which was not produced. The Detective
    survivors of 2026-10-12 that moved a guard, dropped or renamed a record, or altered a count
    were killable only with the ledger recording, which refuses a count that is not a whole
    number."""
    plane = _plane()
    interiors = _interiors(plane)
    ownership = read_ownership_members(interiors, None)
    lenses = read_lenses(plane[None], BOTH)
    with recording() as run:
        reading = read_bundles(ownership, lenses, _measurement(plane, interiors), ())
        silence = read_bundles(None, None, None)
    places = sum(p.places for p in reading.profiles)
    assert places > 0 and len(reading.profiles) >= 2
    assert silence.code == "predecessor_absent"
    assert [(event.name, dict(event.counts)) for event in run.events()] == [
        ("ownership.consumed_by.vectors", {"readings": 1}),
        ("lenses.consumed_by.vectors", {"readings": 1, "places": places}),
        ("objects.consumed_by.vectors", {"readings": 1}),
        ("study.consumed_by.vectors", {"acquisitions": 0}),
        ("vectors.produced", {"profiles": len(reading.profiles), "slab_places": 0}),
        ("study.consumed_by.vectors", {"acquisitions": 0}),
        ("vectors.produced", {"profiles": 0, "slab_places": 0}),
    ]


def test_the_ledger_counts_the_slab_rules_work_as_places_times_acquisitions() -> None:
    """Task 7.10: the counted work of the through-plane banks, read from the ledger and never
    from a profiler: one kernel evaluation per claimed place per other acquisition read."""
    plane = _plane()
    interiors = _interiors(plane)
    ownership = read_ownership_members(interiors, None)
    lenses = read_lenses(plane[None], BOTH)
    others = (_other("B", [0.0, 10.0]), _other("C", [0.0, 10.0]))
    with recording() as run:
        reading = read_bundles(
            ownership, lenses, _measurement(plane, interiors), others
        )
    events = {event.name: event.counts for event in run.events()}
    places = sum(p.places for p in reading.profiles)
    assert places > 0
    assert events["vectors.produced"]["slab_places"] == 2 * places


def test_the_jit_twin_writes_the_same_through_plane_rows_as_the_reference() -> None:
    """Task 7.10, SAME: the twin is admitted only by agreeing with the reference on every row of
    every through-plane bank, on a plane that falls in a slab of one acquisition and in the gap
    of another."""
    pytest.importorskip("numba")
    others = (
        _other("B", [0.0, 10.0]),
        _other("C", [-2.5, 2.5, 7.5], thickness=4.0),
    )
    reference, _, _ = _bundle(others=others, z=1.0, backend="reference")
    twin, _, _ = _bundle(others=others, z=1.0, backend="jit")
    assert reference.backend == "reference"
    assert twin.backend == "jit"
    assert len(reference.profiles) == len(twin.profiles) >= 2
    for first, second in zip(reference.profiles, twin.profiles, strict=True):
        for uid in ("B", "C"):
            assert dict(_bank(first, f"through_plane:{uid}").rows) == dict(
                _bank(second, f"through_plane:{uid}").rows
            )
            assert _bank(first, f"through_plane:{uid}").status == "written"


# ---------------------------------------------------------------- negative


def test_a_missing_lens_record_makes_its_banks_unavailable_never_zero() -> None:
    # MUST NOT: a bank written from nothing would be rows of zero asserting a reading.
    plane = _plane()
    interiors = _interiors(plane)
    ownership = read_ownership_members(interiors, None)
    reading = read_bundles(ownership, None, _measurement(plane, interiors), ())
    assert reading.code == "present"
    for profile in reading.profiles:
        for population, _, _ in MEMBERS:
            bank = _bank(profile, f"own_reading:{population}")
            assert bank.status == "unavailable"
            assert dict(bank.rows) == {}
        assert _bank(profile, "lens_standing").status == "unavailable"


def test_no_ownership_means_no_profile_and_a_named_silence() -> None:
    plane = _plane()
    reading = read_bundles(None, read_lenses(plane[None], BOTH), None, ())
    assert reading.code == "predecessor_absent"
    assert reading.profiles == ()


def test_a_field_that_claims_nothing_writes_no_profile_and_says_so() -> None:
    plane = np.full((10, 10), 50.0)
    interiors = read_interiors(plane, (1.0, 1.0), 10.0, 100.0, OFFSETS)
    ownership = read_ownership_members(interiors, None)
    assert ownership.code == "predecessor_empty"
    reading = read_bundles(
        ownership, read_lenses(plane[None], BOTH), _measurement(plane, interiors), ()
    )
    assert reading.code == "predecessor_empty"
    assert reading.profiles == ()


def test_an_other_acquisition_without_geometry_is_an_unavailable_bank() -> None:
    # MUST NOT: a through-plane bank is never written against a geometry that was not read.
    series = SimpleNamespace(
        row=SimpleNamespace(series_uid="C"), geometry=None, volume=None
    )
    measurement = SimpleNamespace(
        code="no_stacked_volume",
        slice_index=None,
        frame=None,
        interiors=None,
        acquired_plane=None,
        slice_thickness_mm=None,
    )
    reading, _, _ = _bundle(others=((series, measurement),))
    for profile in reading.profiles:
        bank = _bank(profile, "through_plane:C")
        assert bank.status == "unavailable"
        assert dict(bank.rows) == {}


def test_a_backend_outside_the_registry_never_falls_back_and_never_raises() -> None:
    """MUST NOT (task 7.10): a total stage neither raises on a backend it does not know nor runs
    the reference in its place. The through-plane banks are carried unavailable with the refusal
    by name; the banks that need no kernel are unaffected; the request is recorded as made."""
    reading, _, _ = _bundle(others=(_other("B", [0.0, 10.0]),), backend="gpu")
    assert reading.code == "present"
    assert reading.backend == "gpu"
    for profile in reading.profiles:
        bank = _bank(profile, "through_plane:B")
        assert bank.status == "unavailable"
        assert "invalid_backend" in bank.why
        assert dict(bank.rows) == {}
        assert _bank(profile, "lens_standing").status == "written"


def test_no_profile_ever_names_anatomy_or_a_resemblance() -> None:
    reading, _, _ = _bundle()
    text = " ".join(
        [reading.code, reading.why, reading.subject_kind]
        + [
            f"{b.name} {b.source_stage} {b.status} {b.why}"
            for p in reading.profiles
            for b in p.banks
        ]
    ).lower()
    for word in ("femur", "tibia", "bone", "cartilage", "medial", "lateral", "similar"):
        assert word not in text


def test_it_never_raises_however_malformed_the_arguments() -> None:
    plane = _plane()
    interiors = _interiors(plane)
    ownership = read_ownership_members(interiors, None)
    for arguments in (
        (ownership, "lenses", _measurement(plane, interiors)),
        (ownership, read_lenses(plane[None], BOTH), object()),
        (object(), None, None),
        (ownership, None, _measurement(plane, None)),
    ):
        reading = read_bundles(*arguments, ((object(), object()),))
        assert reading.code in ABSENCE_CODES
