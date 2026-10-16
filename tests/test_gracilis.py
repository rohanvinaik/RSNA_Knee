"""Intent tests for the native-scale dark bodies and the gracilis selector."""

import numpy as np

from knee.objects.assignments import (
    OBJECT_CODES,
    SLICE_PARTS,
    Measures,
    TendonBodies,
    assign_plane,
    dark_tendon_bodies,
    gracilis_on_slice,
    native_dark_bodies,
)
from knee.objects.interiors import InteriorRegions

SHAPE = (40, 40)
READINGS = (
    "native_body_labels",
    "native_body_inner_mm",
    "native_body_back_mm",
    "eligible_ids",
    "eligible_distance_mm",
)


def _maps(shape=SHAPE):
    rows, cols = np.indices(shape)
    return rows.astype(float), (shape[1] - cols).astype(float)  # back_mm, inner_mm


def _block(rows, cols, shape=SHAPE):
    mask = np.zeros(shape, dtype=bool)
    mask[rows, cols] = True
    return mask


def _bodies(components, back_mm, inner_mm):
    labels = np.zeros(back_mm.shape, dtype=np.int32)
    for label, mask in enumerate(components, start=1):
        labels[mask] = label
    return TendonBodies(
        labels=labels,
        back_mm=np.asarray([back_mm[m].mean() for m in components], dtype=float),
        inner_mm=np.asarray([inner_mm[m].mean() for m in components], dtype=float),
    )


def _scene():
    """SM (back 19.5, inner 13.5), ST behind it and further inner (back 27.5, inner 23.5), and
    the named bodies' neighbours: the cord (medial to both, in front of ST) and four decoys."""
    back_mm, inner_mm = _maps()
    sm = _block(slice(18, 22), slice(24, 30))
    st = _block(slice(26, 30), slice(14, 18))
    cord = _block(slice(20, 27), slice(3, 6))
    far = _block(slice(4, 8), slice(3, 7))  # eligible but farther from the pair
    medial_to_sm_only = _block(slice(20, 25), slice(20, 23))
    behind_st = _block(slice(33, 37), slice(3, 7))
    lateral = _block(slice(20, 25), slice(33, 37))
    return back_mm, inner_mm, sm, st, cord, (far, medial_to_sm_only, behind_st, lateral)


def _select(bodies, sm, st, back_mm, inner_mm, spacing=(1.0, 1.0), knee="R", **kw):
    return gracilis_on_slice(
        bodies, sm, st, back_mm, inner_mm, np.asarray(spacing), knee, **kw
    )


def test_selects_the_whole_body_medial_to_both_and_in_front_of_the_st_nearest_the_pair():
    back_mm, inner_mm, sm, st, cord, decoys = _scene()
    bodies = _bodies((sm, st, cord, *decoys), back_mm, inner_mm)

    selected, readings, code = _select(bodies, sm, st, back_mm, inner_mm)

    assert code == "identified"
    assert np.array_equal(selected, cord)
    assert set(readings) == set(READINGS)
    # the eligible are the cord and the far one only, and the cord is the nearer
    assert readings["eligible_ids"].tolist() == [3, 4]
    assert readings["eligible_distance_mm"][0] < readings["eligible_distance_mm"][1]


def test_each_relation_is_needed_medial_to_both_in_front_and_clear_of_the_references():
    back_mm, inner_mm, sm, st, _, (_, only_sm, behind, lateral) = _scene()
    for decoy in (only_sm, behind, lateral):
        bodies = _bodies((sm, st, decoy), back_mm, inner_mm)
        selected, readings, code = _select(bodies, sm, st, back_mm, inner_mm)
        assert (
            code == "abstain_no_body_medial_to_both_and_in_front_of_the_semitendinosus"
        )
        assert not selected.any()
        assert readings["eligible_ids"].shape == (0,)
        assert "eligible_distance_mm" not in readings


def test_a_body_overlapping_a_named_reference_is_not_the_gracilis():
    back_mm, inner_mm = _maps()
    sm = _block(slice(18, 22), slice(26, 30))
    st = _block(slice(26, 30), slice(26, 30))
    bar = _block(
        slice(18, 22), slice(10, 30)
    )  # its mean is medial to both, but it holds SM
    bodies = _bodies((bar,), back_mm, inner_mm)

    selected, _, code = _select(bodies, sm, st, back_mm, inner_mm)
    assert code == "abstain_no_body_medial_to_both_and_in_front_of_the_semitendinosus"
    assert not selected.any()

    elsewhere = _block(
        slice(18, 22), slice(34, 38)
    )  # the same bar, with SM named apart from it
    selected, _, code = _select(bodies, elsewhere, st, back_mm, inner_mm)
    assert code == "identified"
    assert np.array_equal(selected, bar)


def test_names_every_missing_prerequisite():
    back_mm, inner_mm, sm, st, cord, _ = _scene()
    bodies = _bodies((cord,), back_mm, inner_mm)
    none = np.zeros(SHAPE, dtype=bool)
    empty = TendonBodies(np.zeros(SHAPE, dtype=np.int32), np.empty(0), np.empty(0))

    for args, kw, expect in (
        ((bodies, sm, st), {"knee": ""}, "abstain_header_names_no_knee"),
        ((bodies, none, st), {}, "abstain_no_semimembranosus_reference"),
        ((bodies, sm, none), {}, "abstain_no_semitendinosus_reference"),
        ((empty, sm, st), {}, "abstain_no_native_dark_body"),
    ):
        selected, readings, code = _select(*args, back_mm, inner_mm, **kw)
        assert code == expect
        assert not selected.any() and selected.shape == SHAPE
        assert not readings  # nothing was measured, so nothing is claimed
    _, readings, _ = _select(bodies, sm, st, back_mm, inner_mm, knee="L")
    assert "native_body_labels" in readings


def test_an_exact_nearest_tie_abstains_and_keeps_the_readings():
    back_mm, inner_mm = _maps()
    sm = _block(slice(20, 21), slice(24, 28))
    st = _block(slice(28, 29), slice(24, 28))
    above = _block(slice(16, 17), slice(10, 11))
    below = _block(slice(24, 25), slice(10, 11))  # mirror of `above` about the pair
    bodies = _bodies((above, below), back_mm, inner_mm)

    selected, readings, code = _select(bodies, sm, st, back_mm, inner_mm)

    assert code == "abstain_tied_nearest_bodies"
    assert not selected.any()
    assert readings["eligible_ids"].tolist() == [1, 2]
    assert readings["eligible_distance_mm"][0] == readings["eligible_distance_mm"][1]


def test_nearest_is_in_physical_distance_not_pixels():
    back_mm, inner_mm = _maps()
    spacing = np.array([3.0, 1.0])
    back_mm, inner_mm = back_mm * spacing[0], inner_mm * spacing[1]
    sm = _block(slice(20, 21), slice(24, 25))
    st = _block(slice(30, 31), slice(24, 25))
    near_in_pixels = _block(
        slice(17, 18), slice(18, 19)
    )  # 3 rows, 6 columns: 6.7 px, 10.8 mm
    near_in_mm = _block(slice(20, 21), slice(14, 15))  # 10 columns: 10 px, 10.0 mm
    bodies = _bodies((near_in_pixels, near_in_mm), back_mm, inner_mm)

    selected, readings, code = _select(bodies, sm, st, back_mm, inner_mm, spacing)

    assert code == "identified"
    assert np.array_equal(selected, near_in_mm)
    assert readings["eligible_distance_mm"][1] < readings["eligible_distance_mm"][0]


def test_shared_measures_give_the_same_answer_as_the_slices_own_distance():
    back_mm, inner_mm, sm, st, cord, decoys = _scene()
    bodies = _bodies((sm, st, cord, *decoys), back_mm, inner_mm)
    basis = np.array([[1.0, 0.0], [0.0, 1.0], [0.0, 0.0]])
    plane = np.zeros(SHAPE)

    alone = _select(bodies, sm, st, back_mm, inner_mm)
    shared = _select(
        bodies, sm, st, back_mm, inner_mm, measures=Measures(None, plane, basis)
    )

    assert shared[2] == alone[2] == "identified"
    assert np.array_equal(shared[0], alone[0])
    assert np.array_equal(
        shared[1]["eligible_distance_mm"], alone[1]["eligible_distance_mm"]
    )


def test_follows_the_transposed_native_axes_and_the_reflected_inner_side():
    back_mm, inner_mm, sm, st, cord, decoys = _scene()
    parts = (sm, st, cord, *decoys)
    spacing = (2.0, 1.0)
    straight, _, code = _select(
        _bodies(parts, back_mm, inner_mm), sm, st, back_mm, inner_mm, spacing
    )
    assert code == "identified"

    # swap the native axes: arrays and pixel pitch swap together
    swapped, _, swapped_code = _select(
        _bodies([p.T for p in parts], back_mm.T, inner_mm.T),
        sm.T,
        st.T,
        back_mm.T,
        inner_mm.T,
        spacing[::-1],
    )
    assert swapped_code == "identified"
    assert np.array_equal(swapped, straight.T)

    # the mirror image of the scene (a left knee): the picture and its positions flip together
    flip = [p[:, ::-1] for p in parts]
    mirrored, _, mirrored_code = _select(
        _bodies(flip, back_mm[:, ::-1], inner_mm[:, ::-1]),
        sm[:, ::-1],
        st[:, ::-1],
        back_mm[:, ::-1],
        inner_mm[:, ::-1],
        spacing,
        knee="L",
    )
    assert mirrored_code == "identified"
    assert np.array_equal(mirrored, straight[:, ::-1])

    # the same picture with the inner side taken the other way round: the other side is medial
    lateral = parts[-1]
    reversed_side, _, reversed_code = _select(
        _bodies(parts, back_mm, -inner_mm), sm, st, back_mm, -inner_mm, spacing
    )
    assert reversed_code == "identified"
    assert np.array_equal(reversed_side, lateral)


def test_leaves_every_input_unchanged_and_retains_plain_arrays():
    back_mm, inner_mm, sm, st, cord, decoys = _scene()
    bodies = _bodies((sm, st, cord, *decoys), back_mm, inner_mm)
    before = [
        a.copy()
        for a in (
            bodies.labels,
            bodies.back_mm,
            bodies.inner_mm,
            sm,
            st,
            back_mm,
            inner_mm,
        )
    ]

    _, readings, _ = _select(bodies, sm, st, back_mm, inner_mm)

    after = (bodies.labels, bodies.back_mm, bodies.inner_mm, sm, st, back_mm, inner_mm)
    assert all(np.array_equal(a, b) for a, b in zip(before, after, strict=True))
    for name, value in readings.items():
        assert isinstance(value, np.ndarray) and value.dtype != object, name
    assert readings["eligible_ids"].dtype == np.int32
    assert readings["native_body_labels"].shape == SHAPE
    assert readings["native_body_inner_mm"].shape == bodies.inner_mm.shape


def test_native_lens_keeps_a_cord_the_shared_lens_rubs_away_and_measures_it_once():
    dark = np.zeros(SHAPE, dtype=bool)
    dark[10:20, 5:8] = True  # a cord three pixels across, 1.5 mm at this pitch
    dark[14, 6] = False  # a one-pixel crack
    dark[30:36, 20] = True  # a seam one pixel thick
    free = np.ones(SHAPE, dtype=bool)
    rows, cols = np.indices(SHAPE)
    back_mm, inner_mm = rows * 0.5, cols * 0.5

    native = native_dark_bodies(dark, free, back_mm, inner_mm)
    shared = dark_tendon_bodies(dark, free, np.array([0.5, 0.5]), back_mm, inner_mm)

    assert not shared.labels[
        10:20, 5:8
    ].any()  # the shared small-body scale takes it out
    label = int(native.labels[14, 6])
    assert label > 0  # kept whole, its crack closed
    body = native.labels == label
    assert native.labels[30:36, 20].sum() == 0  # the thin seam is still rubbed away
    assert np.isclose(native.back_mm[label - 1], back_mm[body].mean())
    assert np.isclose(native.inner_mm[label - 1], inner_mm[body].mean())
    assert native.labels.shape == SHAPE and native.labels.dtype.kind == "i"


def test_native_lens_closes_a_diagonal_crack_keeps_wide_gaps_and_leaves_the_air_out():
    dark = np.zeros(SHAPE, dtype=bool)
    dark[10:16, 10:16] = True
    for step in range(4):
        dark[11 + step, 11 + step] = False  # a crack running along the diagonal
    dark[10:16, 24:27] = True
    dark[10:16, 30:33] = True  # two bodies three columns apart
    free = np.ones(SHAPE, dtype=bool)
    free[:, 10] = False  # the margin or the air: not a body
    back_mm, inner_mm = _maps()

    native = native_dark_bodies(dark, free, back_mm, inner_mm)

    assert not native.labels[:, 10].any()
    assert native.labels[12, 12] > 0 and native.labels[12, 12] == native.labels[13, 14]
    assert native.labels[12, 25] > 0 and native.labels[12, 31] > 0
    assert native.labels[12, 25] != native.labels[12, 31]


def test_empty_low_signal_gives_empty_measurement_arrays():
    back_mm, inner_mm = _maps()
    native = native_dark_bodies(
        np.zeros(SHAPE, dtype=bool), np.ones(SHAPE, dtype=bool), back_mm, inner_mm
    )

    assert not native.labels.any()
    assert native.back_mm.shape == native.inner_mm.shape == (0,)


def test_gracilis_has_its_code_and_a_placeholder_on_every_slice():
    assert OBJECT_CODES["gracilis"] == 41
    assert len(set(OBJECT_CODES.values())) == len(OBJECT_CODES)
    assert OBJECT_CODES["biceps_femoris_tendon"] == 40
    assert OBJECT_CODES["iliotibial_band"] == 39
    assert SLICE_PARTS.count("gracilis") == 1

    plane = np.ones((12, 12))
    zeros = np.zeros(plane.shape, dtype=bool)
    reading = InteriorRegions(
        "measured",
        zeros,
        ~zeros,
        np.zeros(plane.shape),
        np.zeros(plane.shape, dtype=np.int32),
        np.zeros(plane.shape, dtype=np.int32),
    )
    basis = np.array([[1.0, 0.0], [0.0, 1.0], [0.0, 0.0]])

    assigned = assign_plane(plane, reading, basis, knee="R")

    assert assigned.codes["gracilis"] == "abstain_requires_the_semimembranosus_slice"
