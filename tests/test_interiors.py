"""The lens's territories read alone (`interior_regions`) are the territories it reads with its border
readings (`read_interiors`): a run that draws nothing reads the first, a run that draws the second,
and every stage after the lens reads the same arrays from either."""

from dataclasses import fields

import numpy as np

from knee.objects.interiors import (
    InteriorReading,
    InteriorRegions,
    interior_regions,
    read_interiors,
)

OFFSETS = np.arange(-3.0, 3.5, 0.5)


def scene() -> np.ndarray:
    # two bright bodies in a dark field, one reaching the picture's edge, and a row never filled
    plane = np.zeros((40, 50))
    plane[5:20, 5:22] = 100.0
    plane[18:38, 25:50] = 80.0
    plane[0, :] = np.nan
    return plane


def test_the_territories_alone_are_the_territories_read_with_their_borders() -> None:
    full = read_interiors(scene(), (1.0, 1.0), 10.0, 3.0, OFFSETS, "reference")
    alone = interior_regions(scene(), (1.0, 1.0), 10.0, 3.0)
    assert full.labels.max() == 2 and len(full.edge_points_rc)
    for field in fields(InteriorRegions):
        first, second = getattr(full, field.name), getattr(alone, field.name)
        if isinstance(first, np.ndarray):
            assert np.array_equal(first, second), field.name
        else:
            assert first == second, field.name


def test_only_a_full_reading_holds_border_readings() -> None:
    # a full reading is read wherever the territories are; the territories alone hold no border
    full = read_interiors(scene(), (1.0, 1.0), 10.0, 3.0, OFFSETS, "reference")
    alone = interior_regions(scene(), (1.0, 1.0), 10.0, 3.0)
    assert isinstance(full, InteriorRegions)
    assert not isinstance(alone, InteriorReading)
