"""Intent tests for paired patellar retinaculum wall measurements."""

import numpy as np

from knee.objects.assignments import SHELL_MM, Peak, retinacular_walls

MEDIAL = "medial_patellar_retinaculum"
LATERAL = "lateral_patellar_retinaculum"


def _scene(column_spacing=1.0):
    shape = (24, 41)
    rows, cols = np.indices(shape)
    plane = np.full(shape, 60.0)
    labels = np.zeros(shape, dtype=np.int32)
    labels[4:9, 17:24] = 1
    labels[14:19, 17:24] = 2
    patella_target = np.zeros(shape, dtype=bool)
    patella_target[4, 18] = True
    patella_target[6, 22] = True
    femur_target = np.zeros(shape, dtype=bool)
    femur_target[16, 20] = True
    peaks = (Peak(2, 10.0, (16, 20), 0.0),)
    white = np.zeros(shape, dtype=bool)
    white[6:16, 19:22] = True
    plane[white] = 20.0
    plane[6:16, 22] = 5.0
    plane[6:16, 23] = 7.0
    plane[6:16, 18] = 4.0
    plane[6:16, 17] = 6.0
    basis_lps = np.array([[0.0, column_spacing], [1.0, 0.0], [0.0, 0.0]], dtype=float)
    back_mm = rows.astype(float)
    inner_mm = (cols.astype(float) - 20.0) * column_spacing
    available = np.ones(shape, dtype=bool)
    spacing_rc = np.array([1.0, column_spacing])
    return (
        plane,
        white,
        labels,
        peaks,
        patella_target,
        femur_target,
        basis_lps,
        back_mm,
        inner_mm,
        spacing_rc,
        available,
    )


def _resolve(scene):
    return retinacular_walls(*scene)


def test_both_sides_are_found_and_sparse_targets_are_not_excluded():
    scene = _scene()
    arrays, codes = _resolve(scene)

    medial = arrays[MEDIAL]
    lateral = arrays[LATERAL]
    assert codes[MEDIAL] == codes[LATERAL] == "identified"
    assert medial.dtype == lateral.dtype == np.bool_
    assert medial[:, 22].any() and lateral[:, 18].any()
    # This patellar target pixel is also an outboard minimum; targets locate holders only.
    assert scene[4][6, 22] and medial[6, 22]
    assert not np.any(medial & lateral)


def test_absent_reference_or_white_recess_returns_named_abstention():
    scene = _scene()
    no_patella = list(scene)
    no_patella[4] = np.zeros_like(scene[4])
    arrays, codes = _resolve(tuple(no_patella))
    assert codes[MEDIAL] == codes[LATERAL] == "abstain_no_patella_carried"
    assert not arrays[MEDIAL].any() and not arrays[LATERAL].any()

    no_white = list(scene)
    no_white[1] = np.zeros_like(scene[1])
    arrays, codes = _resolve(tuple(no_white))
    assert codes[MEDIAL] == codes[LATERAL] == "abstain_no_fluid_recess_at_the_patella"
    assert not arrays[MEDIAL].any() and not arrays[LATERAL].any()


def test_minimum_is_taken_outboard_of_each_fluid_edge_and_must_be_darker_than_fluid():
    scene = _scene()
    arrays, codes = _resolve(scene)
    assert arrays[MEDIAL][:, 22].any()
    assert arrays[LATERAL][:, 18].any()

    brighter_strip = list(scene)
    brighter_strip[0] = scene[0].copy()
    brighter_strip[0][6:16, (17, 18, 22, 23)] = 30.0
    arrays, codes = _resolve(tuple(brighter_strip))
    assert codes[MEDIAL] == "abstain_no_outboard_wall_minimum"
    assert codes[LATERAL] == "abstain_no_outboard_wall_minimum"
    assert not arrays[MEDIAL].any() and not arrays[LATERAL].any()


def test_contiguous_equal_minima_form_a_band_but_separated_ties_abstain():
    delta = SHELL_MM / 10.0
    scene = list(_scene(delta))
    scene[0] = scene[0].copy()
    scene[0][6:16, 23] = 5.0
    arrays, codes = _resolve(tuple(scene))
    assert codes[MEDIAL] == "identified"
    assert arrays[MEDIAL][6:16, 22:24].all()

    scene = list(_scene(delta))
    scene[0] = scene[0].copy()
    scene[0][6:16, 22] = 4.0
    scene[0][6:16, 24] = 4.0
    scene[0][6:16, 23] = 5.0
    arrays, codes = _resolve(tuple(scene))
    assert codes[MEDIAL] == "abstain_no_outboard_wall_minimum"
    assert not arrays[MEDIAL].any()


def test_transpose_and_inner_axis_reversal_preserve_physical_side_identity():
    scene = _scene()
    arrays, codes = _resolve(scene)
    assert codes[MEDIAL] == codes[LATERAL] == "identified"

    transposed = list(scene)
    for index in (0, 1, 2, 4, 5, 7, 8, 10):
        transposed[index] = scene[index].T
    transposed[3] = tuple(
        Peak(
            peak.territory,
            peak.depth_mm,
            (peak.peak_rc[1], peak.peak_rc[0]),
            peak.superior_mm,
        )
        for peak in scene[3]
    )
    transposed[6] = np.column_stack((scene[6][:, 1], scene[6][:, 0]))
    transposed[9] = scene[9][::-1]
    transposed_arrays, transposed_codes = _resolve(tuple(transposed))
    assert transposed_codes[MEDIAL] == transposed_codes[LATERAL] == "identified"
    assert np.array_equal(transposed_arrays[MEDIAL], arrays[MEDIAL].T)
    assert np.array_equal(transposed_arrays[LATERAL], arrays[LATERAL].T)

    reflected = list(scene)
    reflected[8] = -scene[8]
    reflected_arrays, reflected_codes = _resolve(tuple(reflected))
    assert reflected_codes[MEDIAL] == reflected_codes[LATERAL] == "identified"
    assert np.array_equal(reflected_arrays[MEDIAL], arrays[LATERAL])
    assert np.array_equal(reflected_arrays[LATERAL], arrays[MEDIAL])
