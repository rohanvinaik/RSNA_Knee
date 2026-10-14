"""Drawing retains the exact pairing reading, including an input silence."""

from knee.pictures.pairings import panels
from knee.relations.pairings import read_pairings


def test_absence_is_passed_through_unchanged():
    reading = read_pairings(None, None)
    assert panels(reading) is reading
    assert panels(reading).code == "predecessor_absent"
