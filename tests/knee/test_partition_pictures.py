"""The frames preserve the readings, including their silences; they invent no partition."""

from types import SimpleNamespace

import numpy as np
import pytest

from knee.ownership.claims import OwnershipReading, read_ownership
from knee.pictures.ownership import panels as ownership_panels
from knee.pictures.relations import panels as relations_panels
from knee.relations.shell import Interstice, RelationsReading, read_relations


@pytest.mark.parametrize(
    "source",
    [
        None,
        SimpleNamespace(labels="malformed", available=None),
        SimpleNamespace(
            labels=np.zeros((2, 3), dtype=np.int32),
            available=np.array([[True, False, True], [True, True, True]]),
            code="no_interior_seeds",
        ),
        SimpleNamespace(
            labels=np.array([[1, 0, 2], [0, 0, 2]], dtype=np.int32),
            available=np.array([[True, False, True], [True, True, True]]),
            code="measured",
        ),
    ],
)
def test_ownership_frame_preserves_the_actual_partition_or_absence(source) -> None:
    reading = read_ownership(source)
    frame = ownership_panels(reading)
    assert frame.claims is reading.claims
    assert frame.residual is reading.residual
    for name in (
        "code",
        "why",
        "claimed_places",
        "residual_places",
        "unavailable_places",
        "objects",
    ):
        assert getattr(frame, name) == getattr(reading, name)


def test_no_claims_does_not_erase_the_residual_picture() -> None:
    source = SimpleNamespace(
        labels=np.zeros((2, 2), dtype=np.int32),
        available=np.array([[True, False], [True, True]]),
        code="no_interior_seeds",
    )
    frame = ownership_panels(read_ownership(source))
    assert frame.code == "predecessor_empty"
    np.testing.assert_array_equal(frame.residual, source.available)
    assert frame.residual_places == 3
    assert frame.unavailable_places == 1


def test_drawing_does_not_repair_counts_by_measuring_the_masks() -> None:
    reading = OwnershipReading(
        "present",
        "unaltered",
        np.ones((1, 1), dtype=bool),
        np.zeros((1, 1), dtype=bool),
        19,
        23,
        29,
        31,
    )
    frame = ownership_panels(reading)
    assert (
        frame.claimed_places,
        frame.residual_places,
        frame.unavailable_places,
        frame.objects,
    ) == (
        19,
        23,
        29,
        31,
    )


@pytest.mark.parametrize("source", [None, object(), SimpleNamespace(code="measured")])
def test_relations_absence_is_not_drawn_as_a_study_without_interstices(source) -> None:
    reading = read_relations(source)
    frame = relations_panels(reading)
    assert frame.code == "construction_absent"
    assert frame.why == reading.why
    assert frame.interstices is reading.interstices


def test_relations_renderer_does_not_replace_a_future_reading_with_the_shell() -> None:
    subjects = (Interstice("facing_pair", 3, 7, "series", "a future construction"),)
    frame = relations_panels(RelationsReading("present", "given reading", subjects))
    assert frame.code == "present"
    assert frame.why == "given reading"
    assert frame.interstices is subjects
    assert frame.pairings is None
