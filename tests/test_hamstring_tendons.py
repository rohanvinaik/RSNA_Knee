"""Intent tests for shared dark-body candidates and their tendon selectors."""

import warnings

import numpy as np

from knee.objects.assignments import (
    Peak,
    TendonBodies,
    dark_tendon_bodies,
    semitendinosus_on_slice,
)


def _maps(shape=(24, 30), spacing_rc=(1.0, 1.0), inner_center=15):
    rows, cols = np.indices(shape)
    back_mm = rows.astype(float) * spacing_rc[0]
    inner_mm = (inner_center - cols).astype(float) * spacing_rc[1]
    condyle = Peak(1, 10.0, (2, inner_center), 0.0)
    return back_mm, inner_mm, condyle


def _bodies(components, back_mm, inner_mm):
    labels = np.zeros(back_mm.shape, dtype=np.int32)
    back_means = []
    inner_means = []
    for label, mask in enumerate(components, start=1):
        labels[mask] = label
        back_means.append(float(back_mm[mask].mean()))
        inner_means.append(float(inner_mm[mask].mean()))
    return TendonBodies(
        labels=labels,
        back_mm=np.asarray(back_means, dtype=float),
        inner_mm=np.asarray(inner_means, dtype=float),
    )


def _sm(shape=(24, 30), rows=slice(4, 5), cols=slice(10, 12)):
    mask = np.zeros(shape, dtype=bool)
    mask[rows, cols] = True
    return mask


def test_shared_dark_tendon_bodies_close_cracks_rub_out_thin_seams_and_measure_once():
    dark = np.zeros((32, 32), dtype=bool)
    dark[5:13, 5:11] = True
    dark[8, 7] = False
    dark[20:28, 15] = True
    free = np.ones(dark.shape, dtype=bool)
    rows, cols = np.indices(dark.shape)
    back_mm = rows.astype(float) * 2.0
    inner_mm = cols.astype(float) * 0.5

    bodies = dark_tendon_bodies(dark, free, np.array([2.0, 0.5]), back_mm, inner_mm)

    label = int(bodies.labels[8, 7])
    assert label > 0  # the one-pixel crack is restored in the whole retained body
    assert (
        bodies.labels[20, 15] == 0
    )  # the 0.5 mm seam is rubbed away by the existing scale
    body = bodies.labels == label
    assert np.isclose(bodies.back_mm[label - 1], back_mm[body].mean())
    assert np.isclose(bodies.inner_mm[label - 1], inner_mm[body].mean())


def test_empty_dark_tendon_bodies_returns_empty_measurement_arrays_without_warning():
    dark = np.zeros((12, 17), dtype=bool)
    free = np.ones(dark.shape, dtype=bool)
    back_mm, inner_mm, _ = _maps(shape=dark.shape)

    with warnings.catch_warnings():
        warnings.simplefilter("error")
        bodies = dark_tendon_bodies(dark, free, np.ones(2), back_mm, inner_mm)

    assert bodies.labels.shape == dark.shape
    assert not bodies.labels.any()
    assert bodies.back_mm.shape == (0,)
    assert bodies.inner_mm.shape == (0,)


def test_semitendinosus_requires_both_spatial_relations():
    back_mm, inner_mm, condyle = _maps()
    valid = np.zeros(back_mm.shape, dtype=bool)
    valid[6:9, 11:14] = True
    wrong_side = np.zeros(back_mm.shape, dtype=bool)
    wrong_side[6:9, 17:20] = True
    not_behind = np.zeros(back_mm.shape, dtype=bool)
    not_behind[3, 11:14] = True
    bodies = _bodies((valid, wrong_side, not_behind), back_mm, inner_mm)

    selected, code = semitendinosus_on_slice(
        bodies, _sm(), condyle, back_mm, inner_mm, np.ones(2)
    )

    assert code == "identified"
    assert np.array_equal(selected, valid)
    assert selected.sum() == valid.sum()


def test_semitendinosus_abstains_when_candidates_exist_but_none_meet_both_relations():
    back_mm, inner_mm, condyle = _maps()
    wrong_side = np.zeros(back_mm.shape, dtype=bool)
    wrong_side[6:9, 17:20] = True
    not_behind = np.zeros(back_mm.shape, dtype=bool)
    not_behind[3, 11:14] = True
    bodies = _bodies((wrong_side, not_behind), back_mm, inner_mm)

    selected, code = semitendinosus_on_slice(
        bodies, _sm(), condyle, back_mm, inner_mm, np.ones(2)
    )

    assert bodies.labels.any()
    assert code == "abstain_no_body_meets_both_spatial_relations"
    assert not selected.any()


def test_semitendinosus_selects_nearest_eligible_body_whole():
    back_mm, inner_mm, condyle = _maps()
    near = np.zeros(back_mm.shape, dtype=bool)
    near[6:9, 10:13] = True
    far = np.zeros(back_mm.shape, dtype=bool)
    far[10:13, 3:6] = True
    bodies = _bodies((near, far), back_mm, inner_mm)

    selected, code = semitendinosus_on_slice(
        bodies, _sm(), condyle, back_mm, inner_mm, np.ones(2)
    )

    assert code == "identified"
    assert np.array_equal(selected, near)
    assert selected.sum() == 9


def test_semitendinosus_nearest_uses_physical_spacing():
    spacing = np.array([3.0, 1.0])
    back_mm, inner_mm, condyle = _maps(
        shape=(24, 30), spacing_rc=spacing, inner_center=20
    )
    sm = _sm(shape=back_mm.shape, rows=slice(4, 5), cols=slice(12, 13))
    row_farther_in_pixels = np.zeros(back_mm.shape, dtype=bool)
    row_farther_in_pixels[6, 12] = True  # 2 rows × 3 mm = 6 mm away
    column_farther_in_pixels = np.zeros(back_mm.shape, dtype=bool)
    column_farther_in_pixels[5, 16] = True  # sqrt(3² + 4²) = 5 mm away
    bodies = _bodies(
        (row_farther_in_pixels, column_farther_in_pixels), back_mm, inner_mm
    )

    selected, code = semitendinosus_on_slice(
        bodies, sm, condyle, back_mm, inner_mm, spacing
    )

    assert code == "identified"
    assert np.array_equal(selected, column_farther_in_pixels)


def test_semitendinosus_abstains_on_an_exact_nearest_distance_tie():
    back_mm, inner_mm, _ = _maps(inner_center=20)
    condyle = Peak(1, 10.0, (2, 20), 0.0)
    sm = _sm(shape=back_mm.shape, rows=slice(4, 5), cols=slice(15, 16))
    left = np.zeros(back_mm.shape, dtype=bool)
    left[6, 14] = True
    right = np.zeros(back_mm.shape, dtype=bool)
    right[6, 16] = True
    bodies = _bodies((left, right), back_mm, inner_mm)

    selected, code = semitendinosus_on_slice(
        bodies, sm, condyle, back_mm, inner_mm, np.ones(2)
    )

    assert code == "abstain_tied_nearest_bodies"
    assert not selected.any()


def test_semitendinosus_names_missing_prerequisites_and_empty_candidates():
    back_mm, inner_mm, condyle = _maps()
    candidate = np.zeros(back_mm.shape, dtype=bool)
    candidate[7:9, 10:12] = True
    bodies = _bodies((candidate,), back_mm, inner_mm)
    empty = TendonBodies(
        labels=np.zeros(back_mm.shape, dtype=np.int32),
        back_mm=np.zeros(0, dtype=float),
        inner_mm=np.zeros(0, dtype=float),
    )
    sm = _sm()

    no_reference, no_reference_code = semitendinosus_on_slice(
        bodies, np.zeros_like(sm), condyle, back_mm, inner_mm, np.ones(2)
    )
    no_condyle, no_condyle_code = semitendinosus_on_slice(
        bodies, sm, None, back_mm, inner_mm, np.ones(2)
    )
    no_candidates, no_candidates_code = semitendinosus_on_slice(
        empty, sm, condyle, back_mm, inner_mm, np.ones(2)
    )

    assert no_reference_code == "abstain_no_semimembranosus_reference"
    assert no_condyle_code == "abstain_no_inner_condyle_peak"
    assert no_candidates_code == "abstain_no_dark_body_candidates"
    assert not no_reference.any() and not no_condyle.any() and not no_candidates.any()


def test_semitendinosus_reflects_with_the_patient_inner_axis():
    back_mm, right_inner_mm, condyle = _maps(inner_center=15)
    left_side = np.zeros(back_mm.shape, dtype=bool)
    left_side[7:9, 10:12] = True
    right_side = np.zeros(back_mm.shape, dtype=bool)
    right_side[7:9, 18:20] = True
    bodies = _bodies((left_side, right_side), back_mm, right_inner_mm)
    sm = _sm(shape=back_mm.shape, rows=slice(4, 5), cols=slice(14, 16))

    selected_right, right_code = semitendinosus_on_slice(
        bodies, sm, condyle, back_mm, right_inner_mm, np.ones(2)
    )
    reflected_inner_mm = -right_inner_mm
    reflected_bodies = _bodies((left_side, right_side), back_mm, reflected_inner_mm)
    selected_left, left_code = semitendinosus_on_slice(
        reflected_bodies, sm, condyle, back_mm, reflected_inner_mm, np.ones(2)
    )

    assert right_code == left_code == "identified"
    assert np.array_equal(selected_right, left_side)
    assert np.array_equal(selected_left, right_side)
