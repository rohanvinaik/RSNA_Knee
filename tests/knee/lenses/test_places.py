"""A native digit map is the scalar reading repeated, and every seated member keeps its own."""

from types import SimpleNamespace

import numpy as np
import pytest

from knee.lenses.digits import DIGIT_CODES, digit_code
from knee.lenses.places import (
    CODE_VALUES,
    SILENT,
    STANDING_VALUES,
    place_codes_reference,
    read_lenses,
)
from knee.telemetry import recording

BOTH = SimpleNamespace(
    terciles=(2.0, 4.0),
    foreground_count=8,
    tercile_minimum_population=8,
    split_terciles=(2.0, 4.0),
    split_population_count=8,
)
FIRST_ONLY = SimpleNamespace(
    terciles=(2.0, 4.0), foreground_count=8, tercile_minimum_population=8
)


@pytest.mark.parametrize(
    "edges,count,minimum",
    [
        ((2.0, 4.0), 8, 8),
        ((3.0, 3.0), 8, 8),
        ((4.0, 2.0), 8, 8),
        ((np.nan, 4.0), 8, 8),
        ((2.0, 4.0), 7, 8),
        ((2.0, 4.0), 0, 0),
    ],
)
def test_vector_reference_answers_to_every_scalar_including_silence(
    edges, count, minimum
) -> None:
    values = np.array([[[1.0, 2.0, 3.0, 4.0, 5.0, np.nan, np.inf, -np.inf]]])
    before = values.copy()
    actual = place_codes_reference(values, *edges, count, minimum)
    expected = np.array(
        [
            CODE_VALUES[digit_code(float(v), *edges, count, minimum)]
            for v in values.flat
        ],
        dtype=np.uint8,
    ).reshape(values.shape)
    np.testing.assert_array_equal(actual, expected)
    np.testing.assert_array_equal(values, before)
    assert not actual.flags.writeable


def test_two_acquisitions_use_their_own_pair_without_rescaling() -> None:
    first = read_lenses(
        np.array([[[1.0, 2.0, 3.0, 4.0, 5.0, np.nan]]]),
        SimpleNamespace(
            terciles=(2.0, 4.0), foreground_count=8, tercile_minimum_population=8
        ),
    )
    second = read_lenses(
        np.array([[[10.0, 20.0, 30.0, 40.0, 50.0, np.nan]]]),
        SimpleNamespace(
            terciles=(20.0, 40.0), foreground_count=8, tercile_minimum_population=8
        ),
    )
    one, other = first.members[0], second.members[0]
    assert one.normalisation == other.normalisation == "none"
    assert (one.low_edge, one.high_edge) == (2.0, 4.0)
    assert (other.low_edge, other.high_edge) == (20.0, 40.0)
    np.testing.assert_array_equal(one.digits, other.digits)
    np.testing.assert_array_equal(one.digits, [[[-1, 0, 0, 0, 1, SILENT]]])
    assert one.counts == (1, 3, 1, 1, 0, 0, 0)
    assert not one.digits.flags.writeable


def test_both_members_are_seated_and_each_names_its_own_population() -> None:
    reading = read_lenses(np.array([[[1.0, 3.0, 5.0]]]), BOTH)
    assert tuple(member.population for member in reading.members) == (
        "noise_law_cut",
        "background_split",
    )
    assert all(member.code == "present" for member in reading.members)


def test_a_member_without_its_population_is_silent_and_is_never_filled_from_the_other() -> (
    None
):
    """The forbidden move is a DEFAULT (law 3), and avoiding it is why these are two members."""
    reading = read_lenses(np.array([[[1.0, 2.0, 3.0, 4.0, 5.0, np.nan]]]), FIRST_ONLY)
    present, absent = reading.members
    assert present.code == "present"
    assert absent.code == "item_unread"
    assert absent.low_edge is None and absent.high_edge is None
    assert absent.population_count is None
    assert (absent.digits == SILENT).all()


def test_the_standing_names_which_member_read_each_place() -> None:
    reading = read_lenses(np.array([[[1.0, 2.0, 3.0, 4.0, 5.0, np.nan]]]), FIRST_ONLY)
    assert reading.standing_counts[STANDING_VALUES["first_only"]] == 5
    assert reading.standing_counts[STANDING_VALUES["neither_read"]] == 1
    assert reading.standing_counts[STANDING_VALUES["concur"]] == 0
    assert reading.standing_counts[STANDING_VALUES["dissent"]] == 0


def test_concurrence_and_dissent_are_both_kept_and_neither_is_resolved() -> None:
    volume = np.array([[[1.0, 3.0, 5.0]]])
    concurring = read_lenses(volume, BOTH)
    assert concurring.standing_counts[STANDING_VALUES["concur"]] == 3
    assert concurring.standing_counts[STANDING_VALUES["dissent"]] == 0

    # Same volume, second member reading a different population's pair: 1.0 is below both,
    # 3.0 is `at` for the first and `below` for the second, 5.0 is `above` then `at`.
    dissenting = read_lenses(
        volume,
        SimpleNamespace(
            terciles=(2.0, 4.0),
            foreground_count=8,
            tercile_minimum_population=8,
            split_terciles=(4.0, 6.0),
            split_population_count=8,
        ),
    )
    assert dissenting.standing_counts[STANDING_VALUES["concur"]] == 1
    assert dissenting.standing_counts[STANDING_VALUES["dissent"]] == 2
    # Both members' own digits survive the disagreement unchanged.
    np.testing.assert_array_equal(dissenting.members[0].digits, [[[-1, 0, 1]]])
    np.testing.assert_array_equal(dissenting.members[1].digits, [[[-1, -1, 0]]])


def test_missing_metadata_never_reconstructs_a_population_from_a_share() -> None:
    reading = read_lenses(
        np.ones((1, 2, 2)), SimpleNamespace(terciles=(1.0, 2.0), foreground_share=0.8)
    )
    first = reading.members[0]
    assert first.code == "item_unread"
    assert first.population_count is None
    assert first.low_edge is None
    assert (first.digits == SILENT).all()


def test_small_population_writes_only_named_silence() -> None:
    reading = read_lenses(
        np.ones((1, 2, 2)),
        SimpleNamespace(
            terciles=(1.0, 2.0), foreground_count=7, tercile_minimum_population=8
        ),
    )
    first = reading.members[0]
    assert first.code == "population_too_small"
    assert (first.digits == SILENT).all()
    assert first.counts[CODE_VALUES["population_too_small"]] == 4


@pytest.mark.parametrize(
    "volume,key,code",
    [
        (None, None, "predecessor_absent"),
        ("malformed", object(), "item_unread"),
        (np.empty((0, 2, 2)), object(), "predecessor_empty"),
    ],
)
def test_missing_malformed_and_empty_predecessors_complete_with_named_codes(
    volume, key, code
) -> None:
    reading = read_lenses(volume, key)
    for member in reading.members:
        assert member.code == code
        assert not member.codes.flags.writeable
    assert not reading.standings.flags.writeable


def test_map_counts_and_ledger_are_computed_from_codes_once() -> None:
    with recording() as ledger:
        reading = read_lenses(np.array([[[1.0, 3.0, 5.0, np.nan]]]), FIRST_ONLY)
    for member in reading.members:
        assert sum(member.counts) == member.codes.size
        assert len(member.counts) == len(DIGIT_CODES)
    assert sum(reading.standing_counts) == reading.standings.size
    assert ledger.totals() == {"members": 2, "places": 4, "output_bytes": 20}


def test_no_field_of_the_reading_records_a_resolved_digit() -> None:
    """Resolution is the founder's. A field for it would let a stage take that from him."""
    reading = read_lenses(np.array([[[1.0, 3.0, 5.0]]]), BOTH)
    for forbidden in ("digits", "codes", "low_edge", "high_edge", "resolved"):
        assert not hasattr(reading, forbidden)
