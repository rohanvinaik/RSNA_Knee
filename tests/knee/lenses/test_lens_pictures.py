"""Pictures arrange the stage's values; silence is never rewritten as middle."""

import numpy as np
import pytest

from knee.pictures.lenses import panels


@pytest.mark.parametrize("code", ["present", "no_edges", "predecessor_absent"])
def test_panel_passes_every_value_unchanged_including_silence_and_absence(code):
    codes = np.array([[0, 1, 2, 3]], dtype=np.uint8)
    digits = np.array([[-1, 0, 1, 2]], dtype=np.int8)
    picture = panels(code, "saved reason", codes, digits, None, None, "none")
    assert picture.code == code
    assert picture.why == "saved reason"
    assert picture.codes is codes
    assert picture.digits is digits
    assert picture.low_edge is None and picture.high_edge is None
    assert picture.normalisation == "none"
    assert digits[0, 3] == 2


def test_panel_does_not_slice_or_measure_a_missing_plane():
    codes = np.empty((0, 0), dtype=np.uint8)
    digits = np.empty((0, 0), dtype=np.int8)
    picture = panels(
        "item_unread", "plane unavailable", codes, digits, 2.0, 4.0, "none"
    )
    assert picture.codes is codes and picture.digits is digits
    assert (picture.low_edge, picture.high_edge) == (2.0, 4.0)
    assert picture.code == "item_unread"
