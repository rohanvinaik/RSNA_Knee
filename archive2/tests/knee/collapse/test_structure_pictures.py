"""The structural reading's picture adapter hands the stage's values on and arranges nothing (task 7.1)."""

import math
from dataclasses import replace

import numpy as np
import pytest

from knee.collapse.structure import StructureBars, read_structure
from knee.pictures.collapse import CollapsePanels, panels, structure_panels

CORONAL = np.array([1.0, 0.0, 0.0, 0.0, 0.0, -1.0])
NORMAL = np.array([0.0, 1.0, 0.0])


def _plane() -> np.ndarray:
    plane = np.zeros((60, 60))
    plane[10:50, 15:45] = 100.0
    plane[25:35, 15:45] = 5.0
    return plane


def _reading(plane=None, orientation=CORONAL, normal=NORMAL):
    plane = _plane() if plane is None else plane
    return read_structure(
        plane, orientation, normal, (1.0, 1.0), 5.0, False, StructureBars()
    )


def test_every_value_is_the_stages_own_handed_on_unchanged() -> None:
    plane = _plane()
    reading = _reading(plane)
    frame = structure_panels(plane, reading)
    assert frame.code == reading.code and frame.why == reading.why
    assert frame.axis_code == "rows" and frame.axis == 0
    assert frame.superior_code == "decreasing" and frame.sign == 1.0
    for name in (
        "air",
        "leg",
        "inside",
        "profile",
        "profile_tiles",
        "basins",
        "seam",
        "dark",
        "bodies",
    ):
        assert getattr(frame, name) is getattr(reading, name), name
    assert frame.squint is reading.squint.median
    assert frame.histogram[0] is reading.histogram_counts
    assert frame.histogram[1] is reading.histogram_edges
    assert frame.dip == reading.dip
    assert (
        frame.air_level == reading.air_level and frame.dark_level == reading.dark_level
    )
    assert frame.counts == reading.counts
    np.testing.assert_array_equal(frame.plane, plane)


def test_the_adapter_feeds_the_collapse_panels_it_was_written_for() -> None:
    """`panels()` asked for a leg, a squint, a profile, an axis and a sign; the structural reading
    supplies all five, so the panel the founder designed in 2026-10-10 draws at last."""
    plane = _plane()
    frame = structure_panels(plane, _reading(plane))
    assert frame.axis is not None and frame.squint is not None
    arranged = panels(
        frame.plane, frame.leg, frame.squint, frame.profile, frame.axis, frame.sign
    )
    assert isinstance(arranged, CollapsePanels)
    assert arranged.axis == 0 and arranged.sign == 1.0
    assert arranged.leg.sum() == frame.leg.sum()
    np.testing.assert_array_equal(arranged.profile, frame.profile)


def test_an_increasing_superior_direction_is_the_negative_sign() -> None:
    flipped = CORONAL.copy()
    flipped[5] = 1.0
    frame = structure_panels(_plane(), _reading(orientation=flipped))
    assert frame.superior_code == "increasing" and frame.sign == -1.0


def test_an_axis_that_is_not_in_plane_has_no_image_axis_and_no_sign_is_invented() -> (
    None
):
    axial = np.array([1.0, 0.0, 0.0, 0.0, 1.0, 0.0])
    frame = structure_panels(
        _plane(), _reading(orientation=axial, normal=np.array([0.0, 0.0, 1.0]))
    )
    assert frame.axis_code == "normal" and frame.axis is None
    unread = structure_panels(_plane(), _reading(orientation=None, normal=None))
    assert (
        unread.axis_code == "unreadable" and unread.axis is None and unread.sign == 0.0
    )


def test_a_silent_reading_is_handed_on_as_silence() -> None:
    reading = read_structure(
        None, CORONAL, NORMAL, (1.0, 1.0), 5.0, False, StructureBars()
    )
    frame = structure_panels(np.zeros((0, 0)), reading)
    assert frame.code == "predecessor_absent"
    assert frame.squint is None and frame.profile.shape == (0,) and frame.dip == -1
    assert math.isnan(frame.air_level)


def test_a_code_the_stage_never_says_is_refused_not_drawn() -> None:
    """MUST NOT: label a picture with a word the stage's vocabulary does not hold."""
    reading = _reading()
    with pytest.raises(ValueError, match="unknown_axis_code"):
        structure_panels(_plane(), replace(reading, axis="femoral"))
    with pytest.raises(ValueError, match="unknown_superior_code"):
        structure_panels(_plane(), replace(reading, superior="up"))


def test_the_adapter_computes_nothing_from_the_plane() -> None:
    """MUST NOT: measure. Two different planes with the same reading give the same panels but the
    plane; nothing in the frame is derived from the plane's values."""
    reading = _reading()
    one = structure_panels(_plane(), reading)
    other = structure_panels(np.full((60, 60), 7.0), reading)
    for name in (
        "air",
        "leg",
        "profile",
        "basins",
        "seam",
        "dark",
        "bodies",
        "dip",
        "counts",
    ):
        first, second = getattr(one, name), getattr(other, name)
        assert first is second or first == second
