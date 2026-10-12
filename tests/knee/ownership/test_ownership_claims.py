"""Ownership: the partition, and the residual map that is this stage's whole point.

Every test calls `read_ownership` or `ownership_code` DIRECTLY by name, because Detective routes by
static path.

The load-bearing case is a field that resolves NOTHING. That is not an empty record — it is a field
whose residual is everything, which is the reading worth looking at. `ownership/__init__.py`:
*"A round that claims nothing new hands back explicit unresolved material rather than silently
declaring the parse complete."*
"""

from dataclasses import dataclass

import numpy as np

from knee.absence import CODES
from knee.objects.interiors import read_interiors
from knee.ownership.claims import (
    COMPARISONS,
    OwnershipReading,
    comparison_code,
    members_code,
    ownership_code,
    read_ownership,
    read_ownership_members,
)

OFFSETS = np.array([-2.0, -1.0, 0.0, 1.0, 2.0])


@dataclass
class _Reading:
    """A hand-built stand-in, for fields `read_interiors` cannot produce."""

    labels: object
    available: object
    code: str = "measured"


def _two_bodies():
    """A real reading: two bright bodies with a dark band between them."""
    plane = np.full((24, 24), 100.0)
    plane[10:14, :] = 1.0
    return read_interiors(plane, (1.0, 1.0), 10.0, 1.0, OFFSETS)


def _resolves_nothing():
    """A real reading that seeds no interior: prominence far above the field's depth."""
    return read_interiors(np.full((10, 10), 50.0), (1.0, 1.0), 10.0, 100.0, OFFSETS)


# --------------------------------------------------------------------------------------------
# Positive: what it must do.
# --------------------------------------------------------------------------------------------


def test_a_real_field_partitions_into_claimed_residual_and_unread() -> None:
    reading = read_ownership(_two_bodies())
    assert reading.code == "present"
    total = (
        reading.claimed_places + reading.residual_places + reading.unavailable_places
    )
    assert total == reading.claims.size
    assert reading.objects >= 1


def test_a_field_that_resolves_nothing_still_returns_its_residual_map() -> None:
    """The point of the stage. Nothing claimed means EVERYTHING read is residual."""
    reading = read_ownership(_resolves_nothing())
    assert reading.code == "predecessor_empty"
    assert reading.claimed_places == 0
    assert reading.objects == 0
    assert reading.residual_places == 100
    assert reading.residual.shape == (10, 10)
    assert reading.residual.all()


def test_it_carries_the_predecessors_own_code_forward() -> None:
    """Four distinct upstream reasons must not collapse into one word here."""
    assert read_ownership(_resolves_nothing()).why == "no_interior_seeds"
    assert read_ownership(_two_bodies()).why == "measured"


def test_a_missing_reading_is_named_and_holds_no_places() -> None:
    reading = read_ownership(None)
    assert reading.code == "predecessor_absent"
    assert reading.claims.size == 0


def test_a_field_that_cannot_be_read_as_one_field_is_named() -> None:
    mismatched = _Reading(
        np.zeros((2, 2), dtype=np.int32), np.zeros((3, 3), dtype=bool)
    )
    assert read_ownership(mismatched).code == "invalid_count"


def test_the_returned_arrays_are_frozen_and_the_callers_are_not() -> None:
    interiors = _two_bodies()
    reading = read_ownership(interiors)
    assert not reading.claims.flags.writeable
    assert not reading.residual.flags.writeable


def test_the_pure_decision_names_each_case_it_can_reach() -> None:
    assert ownership_code(False, 0) == "predecessor_absent"
    assert ownership_code(True, -1) == "invalid_count"
    assert ownership_code(True, 0) == "predecessor_empty"
    assert ownership_code(True, 4) == "present"


# --------------------------------------------------------------------------------------------
# Negative: what it must NEVER do.
# --------------------------------------------------------------------------------------------


def test_it_never_discards_a_map_it_could_compute() -> None:
    """Regression guard. A readable field that claimed nothing once came back EMPTY, which lost
    the residual precisely where the residual is the entire reading."""
    reading = read_ownership(_resolves_nothing())
    assert reading.residual.size != 0, "a computable residual map was thrown away"


def test_it_never_counts_an_unread_place_as_residual() -> None:
    """Unread is not unclaimed. A place the acquisition never read is neither."""
    plane = np.full((8, 8), 100.0)
    plane[0, :] = np.nan
    reading = read_ownership(read_interiors(plane, (1.0, 1.0), 10.0, 1.0, OFFSETS))
    assert reading.unavailable_places == 8
    assert not reading.residual[0, :].any()


def test_it_never_returns_a_code_outside_the_shared_vocabulary() -> None:
    for argument in (None, _two_bodies(), _resolves_nothing()):
        assert read_ownership(argument).code in CODES


def test_it_never_raises_however_malformed_the_record() -> None:
    """Total over its argument: a stage that raises breaks the route for every later stage."""
    malformed = (
        _Reading(None, None),
        _Reading(np.zeros((2, 2)), np.zeros((2, 2), dtype=bool)),
        _Reading(np.zeros((2, 2), dtype=np.int32), np.ones((2, 2))),
        _Reading(np.zeros(4, dtype=np.int32), np.zeros(4, dtype=bool)),
        _Reading("not an array", "neither"),
    )
    for argument in malformed:
        assert isinstance(read_ownership(argument), OwnershipReading)


def test_it_never_reports_present_over_a_field_it_could_not_read() -> None:
    assert (
        read_ownership(_Reading(np.zeros((2, 2)), np.zeros((2, 2)))).code != "present"
    )
    assert read_ownership(None).code != "present"


# --------------------------------------------------------------------------------------------
# The members: one partition per parse (task 6.2). Both signs, every call direct by name.
# --------------------------------------------------------------------------------------------


@dataclass
class _Conversation:
    """A stand-in for one SeriesConversation, carrying only the fields the members read."""

    code: str
    concurrent_labels: object
    conditional_labels: object


def _conversed(interiors, code: str = "measured") -> _Conversation:
    """A conversation whose concurrent parse splits the first territory in two."""
    concurrent = interiors.labels.copy()
    rows, cols = np.nonzero(concurrent == 1)
    if len(rows):
        concurrent[rows[0], cols[0]] = 0  # one barrier cell, read and left unclaimed
    return _Conversation(code, concurrent, interiors.labels.copy())


def test_without_a_conversation_only_the_solitary_parse_is_seated() -> None:
    members = read_ownership_members(_two_bodies(), None)
    assert [m.parse for m in members.members] == ["solitary"]
    assert members.code == "present"
    assert members.comparison == "member_absent"
    assert members.disagreement.shape == (0, 0)
    assert "no conversation" in members.why


def test_a_measured_conversation_seats_three_members_and_keeps_their_disagreement() -> (
    None
):
    interiors = _two_bodies()
    members = read_ownership_members(interiors, _conversed(interiors))
    assert [m.parse for m in members.members] == [
        "solitary",
        "concurrent",
        "conditional",
    ]
    assert members.comparison == "compared"
    assert members.disagreeing_places == 1
    assert members.disagreement.shape == interiors.labels.shape
    solitary, concurrent = members.members[0].reading, members.members[1].reading
    assert solitary.claimed_places == concurrent.claimed_places + 1


def test_a_conversation_that_did_not_read_the_series_seats_nothing_from_it() -> None:
    interiors = _two_bodies()
    unread = _Conversation("recipient_unavailable", np.zeros((0, 0), np.int32), None)
    members = read_ownership_members(interiors, unread)
    assert [m.parse for m in members.members] == ["solitary"]
    assert "recipient_unavailable" in members.why


def test_the_pure_decisions_name_each_case_both_signs() -> None:
    assert members_code(()) == "predecessor_absent"
    assert members_code(("predecessor_empty", "present")) == "present"
    assert members_code(("predecessor_absent",)) == "predecessor_absent"
    assert (
        members_code(("predecessor_empty", "predecessor_empty")) == "predecessor_empty"
    )
    assert members_code(("present", "nonsense")) == "invalid_count"
    assert comparison_code(4, 4, True) == "compared"
    assert comparison_code(0, 4, True) == "member_absent"
    assert comparison_code(4, 0, True) == "member_absent"
    assert comparison_code(4, 4, False) == "shape_mismatch"
    assert comparison_code(-1, 4, True) == "invalid_count"


def test_the_stages_silence_is_the_solitary_members_never_a_later_ones() -> None:
    # MUST NOT: with no member present, the stage names the FIRST member's silence -- the
    # solitary parse's, which names the predecessor -- and never a later member's.
    assert members_code(("predecessor_empty", "item_unread")) == "predecessor_empty"
    assert members_code(("item_unread", "predecessor_empty")) == "item_unread"
    assert (
        members_code(("predecessor_absent", "predecessor_empty", "item_unread"))
        == "predecessor_absent"
    )


def test_no_member_is_ever_filled_from_another() -> None:
    """MUST NOT: a conversed parse of the wrong shape is not seated, and the solitary member's
    reading is what `read_ownership` returns for the interiors alone -- never a blend."""
    interiors = _two_bodies()
    wrong = _Conversation(
        "measured", np.zeros((3, 3), np.int32), np.zeros((3, 3), np.int32)
    )
    members = read_ownership_members(interiors, wrong)
    assert [m.parse for m in members.members] == ["solitary"]
    direct = read_ownership(interiors)
    assert members.members[0].reading.claimed_places == direct.claimed_places
    np.testing.assert_array_equal(members.members[0].reading.claims, direct.claims)


def test_members_never_raise_however_malformed_the_arguments() -> None:
    for interiors in (None, object(), _Reading(None, None), _two_bodies()):
        for conversation in (None, object(), 0, _Conversation("measured", None, None)):
            members = read_ownership_members(interiors, conversation)
            assert members.code in CODES
            assert members.comparison in COMPARISONS
            assert len(members.members) >= 1


def test_the_disagreement_is_a_measurement_and_never_a_resolution() -> None:
    """MUST NOT: nothing in the record names a preferred parse or a resolved claim."""
    interiors = _two_bodies()
    members = read_ownership_members(interiors, _conversed(interiors))
    for name in ("winner", "resolved", "preferred", "merged"):
        assert not hasattr(members, name)
    assert members.disagreement.dtype == np.bool_
    assert not members.disagreement.flags.writeable
