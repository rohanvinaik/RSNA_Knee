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

from knee.absence import CODES as ABSENCE_CODES
from knee.collapse.physical import PlaneFrame
from knee.lenses.digits import DIGIT_CODES
from knee.lenses.members import STANDING_CODES
from knee.lenses.places import MEMBERS, read_lenses
from knee.lenses.slabs import SLAB_CODES
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


def _bundle(plane=None, key=BOTH, others=(), z: float = 0.0):
    plane = _plane() if plane is None else plane
    interiors = _interiors(plane)
    ownership = read_ownership_members(interiors, None)
    lenses = read_lenses(plane[None], key)
    reading = read_bundles(ownership, lenses, _measurement(plane, interiors, z), others)
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
        assert set(bank.rows) == {f"edge_kind:{n}" for n in EDGE_KINDS} | {
            f"trace:{n}" for n in TRACE_CODES
        }


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
    plane = _plane()
    interiors = _interiors(plane)
    ownership = read_ownership_members(interiors, None)
    lenses = read_lenses(plane[None], BOTH)
    with recording() as run:
        reading = read_bundles(ownership, lenses, _measurement(plane, interiors), ())
    events = {event.name: event.counts for event in run.events()}
    assert events["vectors.produced"]["profiles"] == len(reading.profiles)
    assert events["lenses.consumed_by.vectors"]["places"] == sum(
        p.places for p in reading.profiles
    )
    assert "ownership.consumed_by.vectors" in events
    assert "objects.consumed_by.vectors" in events


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
