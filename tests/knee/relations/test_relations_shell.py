"""The relations shell, both signs.

Every test calls `read_relations` DIRECTLY by name, because Detective routes by static path and a
call behind a local helper is not a pin.

What this unit must get right is counter-intuitive and is therefore mostly guarded by the negative
sign: the stage answers `construction_absent` for a PERFECTLY GOOD input, and that is correct. The
silence is about a unit missing from our build (task 1.3a, the facing-pair construction), not about
anything missing from the study. The two have opposite remedies.
"""

import numpy as np

from knee.absence import CODES, is_silence
from knee.objects.interiors import read_interiors
from knee.relations.shell import read_relations


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
        assert read_relations(argument).code == "construction_absent"


def test_an_empty_interstice_tuple_is_never_a_finding_of_no_interstice() -> None:
    """A consumer must route on `code`, never on the tuple's length. The emptiness is silence."""
    reading = read_relations(_a_real_reading())
    assert reading.interstices == ()
    assert is_silence(reading.code), (
        "an empty tuple beside a non-silent code would read as 'this knee has no interstice', "
        "which is a negative invented from a missing reading"
    )
