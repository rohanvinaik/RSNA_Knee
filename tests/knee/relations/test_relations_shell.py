"""The relations stage, both signs.

Every test calls `read_relations` DIRECTLY by name, because Detective routes by static path and a
call behind a local helper is not a pin.

What this unit must get right is counter-intuitive and is therefore mostly guarded by the negative
sign: the stage answers `construction_absent` for a PERFECTLY GOOD input, and that is correct. The
silence is about a unit missing from our build (task 1.3a's second obligation, the interstice
extent), not about anything missing from the study. The two have opposite remedies.

Since task 6.3 the stage also READS the sample-supported pairings itself and carries them, so the
positive sign now checks that what it carries is exactly what the pairing unit returns.
"""

from dataclasses import replace

import numpy as np

from knee.absence import CODES, is_silence
from knee.objects.interiors import EDGE_KINDS, dark_bands, read_interiors
from knee.objects.profiles import sample_profiles
from knee.relations.pairings import read_pairings
from knee.relations.shell import KINDS, Interstice, RelationsReading, read_relations
from knee.telemetry import recording


def _a_bracketed_reading():
    """An interiors reading with ONE bracketed profile that pairs: extent 1 across dark to 2."""
    plane = np.tile([8.0, 8.0, 0.0, 0.0, 8.0, 8.0, 8.0], (3, 1))
    offsets = np.arange(-3.0, 4.0)
    interior = read_interiors(plane, (1.0, 1.0), 1.0, 1.0, offsets)
    points, normals = np.array([[1.0, 3.0]]), np.array([[0.0, 1.0]])
    profiles = sample_profiles(plane, points, normals, offsets, (1.0, 1.0))
    low, high, trace, codes = dark_bands(
        profiles, 1.0, np.array([EDGE_KINDS["low_signal"]]), points, normals, (1, 1)
    )
    return replace(
        interior,
        edge_points_rc=points,
        edge_normals_rc=normals,
        edge_regions=np.array([1], dtype=np.int32),
        profiles=profiles,
        band_low_mm=low,
        band_high_mm=high,
        trace_points_rc=trace,
        trace_codes=codes,
    )


def _a_real_reading():
    """A genuine InteriorReading: two bright bodies with a dark band between them."""
    plane = np.full((24, 24), 100.0)
    plane[10:14, :] = 1.0
    return read_interiors(
        plane,
        (1.0, 1.0),
        split=10.0,
        prominence_mm=1.0,
        offsets_mm=np.array([-2.0, -1.0, 0.0, 1.0, 2.0]),
    )


# --------------------------------------------------------------------------------------------
# Positive: what it must do.
# --------------------------------------------------------------------------------------------


def test_it_names_the_missing_construction_when_there_is_no_input() -> None:
    assert read_relations(None).code == "construction_absent"


def test_it_names_the_missing_construction_for_a_perfectly_good_input() -> None:
    """The whole point of the unit: a good reading does not make the missing unit appear."""
    assert read_relations(_a_real_reading()).code == "construction_absent"


def test_it_constructs_no_interstice() -> None:
    assert read_relations(_a_real_reading()).interstices == ()


def test_its_reason_names_the_construction_rather_than_the_study() -> None:
    why = read_relations(None).why
    assert "1.3a" in why
    assert "has not been built" in why


def test_its_code_is_a_silence_in_the_shared_vocabulary() -> None:
    assert is_silence(read_relations(None).code)


def test_it_carries_the_pairing_reading_of_its_predecessor() -> None:
    """Task 6.3: the pairing unit's own reading, unchanged, from inside the stage."""
    interiors = _a_real_reading()
    carried = read_relations(interiors, (1.0, 1.0)).pairings
    direct = read_pairings(interiors, (1.0, 1.0))
    assert carried is not None
    assert carried.code == direct.code
    assert dict(carried.counts) == dict(direct.counts)
    np.testing.assert_array_equal(carried.outcome_codes, direct.outcome_codes)
    np.testing.assert_array_equal(carried.source_labels, direct.source_labels)


def test_its_pairing_names_its_own_silence_when_there_is_no_input() -> None:
    pairings = read_relations(None).pairings
    assert pairings is not None
    assert pairings.code == "predecessor_absent"


def test_the_ledger_records_exactly_what_the_stage_read_and_produced() -> None:
    """Task 6.5: consumption is recorded by THIS stage at the point of reading, with the counts
    it read, and production with what it made. One bracketed profile pairs, so the counts are 1."""
    with recording() as run:
        reading = read_relations(_a_bracketed_reading(), (1.0, 1.0))
    assert reading.pairings is not None
    assert reading.pairings.counts["paired"] == 1
    assert [(e.name, dict(e.counts)) for e in run.events()] == [
        ("objects.consumed_by.relations", {"interiors": 1}),
        (
            "pairings.produced",
            {"profiles": 1, "paired": 1, "footprint_read_upper_bound": 8},
        ),
        ("pairings.consumed_by.relations", {"profiles": 1, "paired": 1}),
        ("relations.produced", {"interstices": 0, "pairs": 1}),
    ]


def test_the_ledger_counts_nothing_read_when_nothing_was_handed_over() -> None:
    with recording() as run:
        read_relations(None)
    assert [(e.name, dict(e.counts)) for e in run.events()] == [
        ("objects.consumed_by.relations", {"interiors": 0}),
        (
            "pairings.produced",
            {"profiles": 0, "paired": 0, "footprint_read_upper_bound": 0},
        ),
        ("pairings.consumed_by.relations", {"profiles": 0, "paired": 0}),
        ("relations.produced", {"interstices": 0, "pairs": 0}),
    ]


def test_the_ledger_records_no_pairing_attempt_for_a_malformed_predecessor() -> None:
    # MUST NOT: a malformed predecessor is counted as nothing read, and no pairing is produced;
    # a truthy non-reading (the integer 1) must not be counted as an interiors reading.
    with recording() as run:
        read_relations(1, (1.0, 1.0))
    assert [(e.name, dict(e.counts)) for e in run.events()] == [
        ("objects.consumed_by.relations", {"interiors": 0}),
        ("pairings.consumed_by.relations", {"profiles": 0, "paired": 0}),
        ("relations.produced", {"interstices": 0, "pairs": 0}),
    ]


def test_the_interstice_record_and_its_kinds_are_declared_structurally() -> None:
    record = Interstice("facing_pair", 3, 7, "series", "test")
    assert record.kind in KINDS
    assert isinstance(
        RelationsReading("construction_absent", "w", (record,)), RelationsReading
    )
    for word in ("femur", "tibia", "patella", "meniscus", "medial", "lateral", "bone"):
        assert all(word not in kind for kind in KINDS)


# --------------------------------------------------------------------------------------------
# Negative: what it must NEVER do.
# --------------------------------------------------------------------------------------------


def test_it_never_blames_the_study_for_a_unit_missing_from_the_build() -> None:
    """The load-bearing must-not. A predecessor code here would send the next session hunting
    the corpus for a gap that is in our own work, and the remedies are opposite."""
    for argument in (None, _a_real_reading(), object(), 0, "", []):
        code = read_relations(argument).code
        assert code != "predecessor_absent"
        assert code != "predecessor_empty"
        assert code != "item_unread"


def test_it_never_reports_a_reading_it_did_not_make() -> None:
    assert read_relations(_a_real_reading()).code != "present"


def test_it_never_returns_a_code_outside_the_shared_vocabulary() -> None:
    for argument in (None, _a_real_reading(), object(), 0):
        assert read_relations(argument).code in CODES


def test_it_never_raises_however_malformed_the_argument() -> None:
    """Total over its argument: a stage that raises breaks the route for every later stage."""

    class Hostile:
        def __eq__(self, other: object) -> bool:
            raise RuntimeError("must not be reached")

        def __bool__(self) -> bool:
            raise RuntimeError("must not be reached")

    for argument in (Hostile(), float("nan"), b"", {}, type):
        reading = read_relations(argument)
        assert reading.code == "construction_absent"
        # MUST NOT: a malformed predecessor is never handed to the pairing unit to raise on,
        # and the absence of a pairing is explained rather than left bare.
        assert reading.pairings is None
        assert "no pairing was attempted" in reading.why


def test_an_empty_interstice_tuple_is_never_a_finding_of_no_interstice() -> None:
    """A consumer must route on `code`, never on the tuple's length. The emptiness is silence."""
    reading = read_relations(_a_real_reading())
    assert reading.interstices == ()
    assert is_silence(reading.code), (
        "an empty tuple beside a non-silent code would read as 'this knee has no interstice', "
        "which is a negative invented from a missing reading"
    )


def test_a_retained_pair_never_becomes_an_interstice() -> None:
    """MUST NOT: sample support for a relation is not the relation. However many pairs the
    pairing unit retains, the stage constructs nothing from them."""
    plane = np.tile([8.0, 8.0, 0.0, 0.0, 8.0, 8.0, 8.0], (3, 1))
    interiors = read_interiors(plane, (1.0, 1.0), 1.0, 1.0, np.arange(-3.0, 4.0))
    reading = read_relations(interiors, (1.0, 1.0))
    assert reading.pairings is not None
    assert reading.interstices == ()
    assert reading.code == "construction_absent"
