"""The squint stack's own proof gate (its CONTRACT): the corner tile's centre is the centre of the
pixels it holds, half a tile in from the slice origin along both in-plane directions, and a tile's
centre maps back to native within half a pixel."""

import numpy as np

from knee.collapse.physical import PlaneFrame, physical_squint
from knee.collapse.squint_stack import tile_centres_lps

POSITION = (10.0, -20.0, 30.0)
# Columns toward the back, rows downward: a sagittal slice.
ORIENTATION = (0.0, 1.0, 0.0, 0.0, 0.0, -1.0)
SPACING = (0.5, 0.4)  # between rows, between columns


def centres() -> tuple[PlaneFrame, np.ndarray, np.ndarray, tuple[int, int]]:
    frame = PlaneFrame.from_dicom(POSITION, ORIENTATION, SPACING)
    squint = physical_squint(np.ones((100, 120)), frame.spacing_rc, 10.0)
    return (
        frame,
        tile_centres_lps(frame, squint.bounds_rc),
        squint.bounds_rc,
        squint.tile_shape_rc,
    )


def test_the_corner_tiles_centre_is_half_a_tile_in_from_the_origin():
    _, placed, _, (rows, cols) = centres()
    down = np.array([0.0, 0.0, -1.0]) * SPACING[0]
    back = np.array([0.0, 1.0, 0.0]) * SPACING[1]
    # the centre of the pixels the tile holds: (n - 1) / 2 steps in from its first pixel
    expected = np.asarray(POSITION) + (rows - 1) / 2.0 * down + (cols - 1) / 2.0 * back
    assert np.allclose(placed[0, 0], expected)


def test_a_tile_centre_maps_back_to_native_within_half_a_pixel():
    frame, placed, bounds, _ = centres()
    r0, r1, c0, c1 = bounds[3, 4]
    native = frame.to_native(placed[3, 4][None, :])[0]
    assert abs(native[0] - (r0 + r1 - 1) / 2.0) <= 0.5
    assert abs(native[1] - (c0 + c1 - 1) / 2.0) <= 0.5
