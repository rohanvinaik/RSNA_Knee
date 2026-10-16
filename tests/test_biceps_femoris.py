"""The proximal biceps femoris tendon: the dark cord joining the posterior thigh muscle to the
fibular head, on the slice just beyond the head's lateral face (module note, its paragraph)."""

import numpy as np
import pytest

from knee.collapse.physical import PlaneFrame
from knee.objects.assignments import (
    BONE_DISC_MM2,
    HEAD_SLICE_STATUS,
    OBJECT_CODES,
    SHELL_MM,
    SLICE_PARTS,
    Measures,
    distance_from,
    fibula_like_head,
    head_area_mm2,
    lateral_to_the_head,
    places_on_slice,
    projected_places,
    proximal_biceps_on_slice,
    smoothed_along_the_leg,
    twin_marrow_light,
    unique_largest,
)

# rows run down the leg (1 mm each), columns toward the patient's back (1 mm each)
SAGITTAL = np.asarray([[0.0, 0.0], [0.0, 1.0], [-1.0, 0.0]])
H, W = 130, 60
LIGHT, TWIN_LIGHT = 300.0, 60.0
SPACING = np.asarray([1.0, 1.0])


def scene(
    belly=(5, 46, 12, 48),
    cord=(50, 105, 22, 32),
    head=(105, 121, 20, 38),
    extra_belly=None,
    extra_cord=None,
):
    """Fat-bright plane and laid twin: an intermediate background, a dark muscle belly (grey with
    fat suppressed), a cord dark in both acquisitions down to the head, and the head's bright
    marrow (the fibula's own light, dark with fat suppressed); the fibula's projected places."""
    plane = np.full((H, W), 150.0)
    twin = np.full((H, W), 150.0)
    for box, dark, grey in (
        (belly, 60.0, 120.0),
        (extra_belly, 60.0, 120.0),
        (cord, 30.0, 40.0),
        (extra_cord, 30.0, 40.0),
        (head, LIGHT, TWIN_LIGHT),
    ):
        if box is not None:
            r0, r1, c0, c1 = box
            plane[r0:r1, c0:c1], twin[r0:r1, c0:c1] = dark, grey
    target = np.zeros((H, W), dtype=bool)
    target[108:111, 26:30] = True
    return plane, twin, target


def head_of(plane, target):
    head, code = fibula_like_head(plane, target, LIGHT)
    assert code == "identified"
    return head


def run(plane, twin, head, basis=SAGITTAL, light=LIGHT, twin_light=TWIN_LIGHT, **kw):
    return proximal_biceps_on_slice(plane, twin, basis, light, twin_light, head, **kw)


def expected_cord() -> np.ndarray:
    """The cord down to the last row more than SHELL_MM from the head's marrow (row 105)."""
    cord = np.zeros((H, W), dtype=bool)
    cord[50:103, 22:32] = True
    return cord


def test_the_positive_scene_names_the_cord_between_the_muscle_and_the_head() -> None:
    plane, twin, target = scene()
    head = head_of(plane, target)
    mask, readings, code = run(plane, twin, head)
    assert code == "identified"
    assert mask.dtype == np.dtype(bool) and np.array_equal(mask, expected_cord())
    assert int(readings["piece_count"]) == 1 and int(readings["selected_piece"]) == 1
    assert readings["piece_competent"].tolist() == [True]
    assert float(readings["head_top_mm"]) == -105.0
    assert float(readings["muscle_bottom_mm"]) == -45.0
    assert float(readings["piece_area_mm2"][0]) == 530.0
    # provenance: the lights the rule weighed against and the window it smoothed over
    assert float(readings["fibula_marrow_light_fat_bright"]) == LIGHT
    assert float(readings["fibula_marrow_light_fat_suppressed"]) == TWIN_LIGHT
    assert int(readings["smoothing_window_pixels"]) == 5
    assert int(readings["leg_axis"]) == 0
    # every map the rule made is kept, as an array and never an object
    for name in ("muscle_belly", "between_muscle_and_head", "dark_piece_candidates"):
        assert name in readings
    assert all(isinstance(v, np.ndarray) for v in readings.values())
    assert all(v.dtype != np.dtype(object) for v in readings.values())


def test_the_cord_is_below_the_belly_above_the_head_and_dark_in_both() -> None:
    plane, twin, target = scene()
    mask, readings, _ = run(plane, twin, head_of(plane, target))
    up = readings["superior_mm"]
    assert up[mask].max() < float(readings["muscle_bottom_mm"])
    assert up[mask].min() > float(readings["head_top_mm"])
    assert (readings["smoothed_fat_bright"][mask] <= 0.3 * LIGHT).all()
    assert (readings["smoothed_fat_suppressed_twin"][mask] <= TWIN_LIGHT).all()
    # the belly is as dark as the cord without suppression, which alone does not make it the cord
    assert readings["dark_fat_bright"][readings["muscle_belly"]].all()
    assert not readings["tendon_like"][readings["muscle_belly"]].any()


def test_the_cord_up_against_the_head_is_dark_but_not_taken_within_the_cortex_reach() -> (
    None
):
    plane, twin, target = scene()
    mask, readings, _ = run(plane, twin, head_of(plane, target))
    assert readings["tendon_like"][
        103:105, 22:32
    ].all()  # dark in both, against the head
    assert not mask[103:].any()
    marrow = readings["marrow_bodies"]
    assert marrow[readings["head_region"]].all()
    assert distance_from(marrow, SPACING)[mask].min() > SHELL_MM


def test_nothing_within_a_marrow_bodys_reach_is_taken_either() -> None:
    plane, twin, target = scene()
    # another thick bright body, 2 mm from the cord's side: its cortex is not the cord
    plane[60:80, 33:49], twin[60:80, 33:49] = LIGHT, TWIN_LIGHT
    mask, readings, code = run(plane, twin, head_of(plane, target))
    assert code == "identified"
    near = distance_from(readings["marrow_bodies"], SPACING) <= SHELL_MM
    assert (readings["tendon_like"] & readings["between_muscle_and_head"] & near).any()
    assert not (mask & near).any()
    assert not mask[68:72, 31].any() and mask[50:56, 31].all()


def test_the_cord_below_the_muscle_is_required_not_one_above_it() -> None:
    plane, twin, target = scene(belly=(60, 101, 12, 48), cord=(5, 50, 22, 32))
    mask, readings, code = run(plane, twin, head_of(plane, target))
    assert code == "abstain_nothing_dark_between_the_muscle_and_the_head"
    assert not mask.any() and readings["tendon_like"][5:50, 22:32].any()
    assert int(readings["piece_count"]) == 0


def test_a_muscle_below_the_head_is_not_a_belly_above_it() -> None:
    plane, twin, target = scene()
    head = head_of(plane, target)
    mask, readings, code = run(plane[::-1], twin[::-1], head[::-1])
    assert code == "abstain_no_muscle_belly_above_the_head"
    assert not mask.any()
    # refused before the belly was found: no map of it is claimed
    assert "muscle_belly" not in readings and "piece_count" not in readings
    assert readings["muscle_bodies"].any()


@pytest.mark.parametrize(
    "case, expected",
    [
        ("no_head", "abstain_no_fibular_head_on_the_slice"),
        ("no_belly", "abstain_no_muscle_belly_above_the_head"),
        ("no_cord", "abstain_nothing_dark_between_the_muscle_and_the_head"),
        ("short_cord", "abstain_no_competent_piece_joins_the_muscle_and_the_head"),
    ],
)
def test_each_missing_reference_has_its_own_named_refusal(case, expected) -> None:
    plane, twin, target = scene()
    head = head_of(plane, target)
    if case == "no_head":
        head = np.zeros_like(head)
    if case == "no_belly":
        plane[5:46, 12:48], twin[5:46, 12:48] = 150.0, 150.0
    if case == "no_cord":
        plane[50:105, 22:32], twin[50:105, 22:32] = 150.0, 150.0
    if case == "short_cord":  # a cord that reaches neither the belly nor the head
        plane[50:105, 22:32], twin[50:105, 22:32] = 150.0, 150.0
        plane[70:85, 22:32], twin[70:85, 22:32] = 30.0, 40.0
    mask, readings, code = run(plane, twin, head)
    assert code == expected and not mask.any()
    assert mask.shape == plane.shape and mask.dtype == np.dtype(bool)
    assert all(v.dtype != np.dtype(object) for v in readings.values())
    if case == "short_cord":
        assert readings["piece_count"] == 1 and not readings["piece_competent"].any()
        assert float(readings["piece_reach_to_head_mm"][0]) > 10.0


def test_each_prerequisite_of_the_slice_has_its_own_named_refusal() -> None:
    plane, twin, target = scene()
    head = head_of(plane, target)
    axial = np.asarray([[0.0, 1.0], [1.0, 0.0], [0.0, 0.0]])
    coronal = np.asarray([[0.0, 1.0], [0.0, 0.0], [-1.0, 0.0]])
    nothing = np.full(plane.shape, np.nan)
    cases = [
        (
            {"fat_suppressed": True},
            "abstain_marrow_as_dark_as_a_ligament_with_fat_suppression",
        ),
        ({"basis": coronal}, "abstain_front_to_back_runs_through_the_plane"),
        ({"basis": axial}, "abstain_leg_runs_through_the_plane"),
        ({"light": 0.0}, "abstain_no_fibula_marrow_light"),
        ({"light": float("nan")}, "abstain_no_fibula_marrow_light"),
        ({"light": -5.0}, "abstain_no_fibula_marrow_light"),
        ({"twin_light": 0.0}, "abstain_no_suppressed_marrow_light"),
        ({"twin_light": float("inf")}, "abstain_no_suppressed_marrow_light"),
        ({"twin_light": float("nan")}, "abstain_no_suppressed_marrow_light"),
    ]
    for kw, expected in cases:
        mask, readings, code = run(plane, twin, head, **kw)
        assert code == expected and not mask.any() and not readings
    mask, readings, code = run(plane, nothing, head)
    assert code == "abstain_no_twin_on_the_slice" and not mask.any() and not readings
    mask, _, code = run(np.zeros((0, 0)), np.zeros((0, 0)), np.zeros((0, 0), bool))
    assert code == "abstain_empty_slice" and mask.shape == (0, 0)


def test_malformed_inputs_are_refused_loudly_not_read() -> None:
    plane, twin, target = scene()
    head = head_of(plane, target)
    with pytest.raises(ValueError, match="share a 2d shape|same|share"):
        run(plane, twin[:-1], head)
    with pytest.raises(ValueError, match="share"):
        run(plane, twin, head[:, :-1])
    with pytest.raises(ValueError, match="invalid_lps_basis"):
        run(plane, twin, head, basis=SAGITTAL[:2])
    with pytest.raises(ValueError, match="invalid_lps_basis"):
        run(plane, twin, head, basis=np.full((3, 2), np.nan))
    with pytest.raises(ValueError, match="invalid_lps_basis"):
        run(plane, twin, head, basis=np.zeros((3, 2)))


def test_the_belly_and_the_cord_ignore_the_acquisitions_scales() -> None:
    plane, twin, target = scene()
    head = head_of(plane, target)
    base_mask, base, _ = run(plane, twin, head)
    # each acquisition has its own gain, and the marrow's light in each moves with it
    mask, readings, code = run(
        plane * 7.0, twin * 0.25, head, light=LIGHT * 7.0, twin_light=TWIN_LIGHT * 0.25
    )
    assert code == "identified" and np.array_equal(mask, base_mask)
    for name in ("dark_fat_bright", "tendon_like", "muscle_like", "marrow_bodies"):
        assert np.array_equal(readings[name], base[name])
    # the fibula's own marrow light carries the scale: the same pixels against the old light
    # are no longer dark, so nothing is named
    _, _, unscaled = run(plane * 7.0, twin, head)
    assert unscaled == "abstain_no_muscle_belly_above_the_head"


ORIENTATIONS = {
    "transposed": (
        lambda a: a.T,
        SAGITTAL[:, ::-1],
        lambda m: m.T,
        1,
    ),
    "columns_reflected": (
        lambda a: a[:, ::-1],
        SAGITTAL * np.asarray([[1.0, -1.0]] * 3),
        lambda m: m[:, ::-1],
        0,
    ),
    "rows_reflected": (
        lambda a: a[::-1],
        SAGITTAL * np.asarray([[-1.0, 1.0]] * 3),
        lambda m: m[::-1],
        0,
    ),
}


@pytest.mark.parametrize("name", sorted(ORIENTATIONS))
def test_native_orientation_follows_the_basis_not_the_rows(name) -> None:
    plane, twin, target = scene()
    head = head_of(plane, target)
    move, basis, back, leg_axis = ORIENTATIONS[name]
    mask, readings, code = run(move(plane), move(twin), move(head), basis=basis)
    assert code == "identified"
    assert np.array_equal(back(mask), expected_cord())
    assert int(readings["leg_axis"]) == leg_axis
    # the same through the slice's shared measures
    kept, _, kept_code = run(
        move(plane),
        move(twin),
        move(head),
        basis=basis,
        measures=Measures(None, move(plane), basis),
    )
    assert kept_code == "identified" and np.array_equal(kept, mask)


def test_the_filter_never_reads_an_unseen_pixel_as_a_zero() -> None:
    values = np.asarray([np.nan, np.nan, 50.0, 70.0, 70.0, 70.0, 70.0, 70.0])[:, None]
    smooth, window = smoothed_along_the_leg(values, SAGITTAL, 3.0)
    assert window == 5
    # every pixel whose window holds an unseen one has no reading, not a median over zeros
    assert np.isnan(smooth[:4]).all()
    assert smooth[4:, 0].tolist() == [70.0] * 4
    # where the whole window is seen it is the plain median, here along the columns
    seen = np.arange(9.0)[None, :]
    flat, _ = smoothed_along_the_leg(seen, SAGITTAL[:, ::-1], 3.0)
    assert flat[0, 2:7].tolist() == [2.0, 3.0, 4.0, 5.0, 6.0]
    # a window too long for the image is supported by its edge, not unseen
    short, _ = smoothed_along_the_leg(np.full((3, 1), 8.0), SAGITTAL, 3.0)
    assert short[:, 0].tolist() == [8.0, 8.0, 8.0]


def test_twin_pixels_the_twin_does_not_see_make_no_darkness() -> None:
    plane, twin, target = scene()
    head = head_of(plane, target)
    twin[70:73, 20:34] = (
        np.nan
    )  # a band across the cord the twin's picture does not reach
    with np.errstate(all="raise"):
        mask, readings, code = run(plane, twin, head)
    # no reading within the filter's reach of the gap, so the cord does not run through it
    assert not readings["tendon_like"][68:75, 22:32].any()
    assert readings["tendon_like"][50:68, 22:32].all()
    assert not mask[68:75].any()
    assert int(readings["piece_count"]) == 2 and not readings["piece_competent"].any()
    assert code == "abstain_no_competent_piece_joins_the_muscle_and_the_head"
    assert np.isnan(readings["smoothed_fat_suppressed_twin"][70, 25])


def test_pixels_that_are_not_finite_in_the_acquired_slice_are_unread_too() -> None:
    plane, twin, target = scene()
    head = head_of(plane, target)
    plane[70:73, 20:34] = np.nan
    mask, readings, code = run(plane, twin, head)
    assert not readings["dark_fat_bright"][68:75, 22:32].any()
    assert not mask[68:75].any()
    assert code == "abstain_no_competent_piece_joins_the_muscle_and_the_head"


def test_two_exactly_equal_largest_bellies_abstain() -> None:
    plane, twin, target = scene(belly=(5, 46, 2, 26), extra_belly=(5, 46, 34, 58))
    mask, readings, code = run(plane, twin, head_of(plane, target))
    assert code == "abstain_tied_muscle_bellies" and not mask.any()
    assert readings["muscle_body_labels"].max() == 2
    # a larger one is told apart by its size
    plane, twin, target = scene(belly=(5, 46, 2, 26), extra_belly=(5, 46, 30, 58))
    assert run(plane, twin, head_of(plane, target))[2] == "identified"


def test_two_exactly_equal_competent_pieces_abstain() -> None:
    plane, twin, target = scene(
        belly=(5, 46, 2, 58), cord=(50, 105, 8, 18), extra_cord=(50, 105, 40, 50)
    )
    mask, readings, code = run(plane, twin, head_of(plane, target))
    assert code == "abstain_tied_competent_pieces" and not mask.any()
    assert readings["piece_competent"].tolist() == [True, True]
    assert "selected_piece" not in readings


def test_inputs_are_left_as_they_were() -> None:
    plane, twin, target = scene()
    head = head_of(plane, target)
    before = (plane.copy(), twin.copy(), head.copy())
    run(plane, twin, head)
    assert all(
        np.array_equal(a, b) for a, b in zip(before, (plane, twin, head), strict=True)
    )


def test_the_head_is_the_marrow_like_body_holding_the_most_fibula_places() -> None:
    plane = np.full((30, 40), 100.0)
    plane[2:12, 2:12] = LIGHT  # a larger body
    plane[18:25, 20:30] = LIGHT  # a smaller one
    target = np.zeros(plane.shape, dtype=bool)
    target[5, 5] = target[6, 6] = True
    target[20:23, 22] = True
    head, code = fibula_like_head(plane, target, LIGHT)
    assert code == "identified"
    assert head[18:25, 20:30].all() and head.sum() == 70  # holds three places, not two
    # a body's brightness must be the fibula's own: brighter than the band, none is taken
    brighter = np.where(plane == LIGHT, 3.0 * LIGHT, plane)
    assert fibula_like_head(brighter, target, LIGHT)[1] == (
        "abstain_no_marrow_like_body_at_the_fibula"
    )


def test_the_head_morphology_is_one_native_pixel_and_names_what_it_does() -> None:
    plane = np.full((30, 40), 100.0)
    plane[5:20, 5:20] = LIGHT
    plane[3, 3] = LIGHT  # a speck
    plane[12, 20:23] = LIGHT  # a one-pixel bridge to a neighbour...
    plane[8:16, 23:31] = LIGHT  # ... a body of its own
    plane[5:20, 12] = 100.0  # and a one-pixel crack splitting the head
    target = np.zeros(plane.shape, dtype=bool)
    target[10, 8] = True
    head, code = fibula_like_head(plane, target, LIGHT)
    assert code == "identified"
    assert not head[3, 3] and not head[12, 20:23].any()
    assert not head[
        8:16, 23:31
    ].any()  # the bridge is cut, so the neighbour is not the head
    # an opening closes no crack: the head is the side of the crack the fibula is on
    assert head[5:20, 5:12].all() and not head[5:20, 13:20].any()


def test_no_head_is_made_up_for_what_cannot_be_read() -> None:
    plane = np.full((20, 20), LIGHT)
    target = np.zeros(plane.shape, dtype=bool)
    for light, code in (
        (0.0, "abstain_no_fibula_marrow_light"),
        (float("nan"), "abstain_no_fibula_marrow_light"),
        (-1.0, "abstain_no_fibula_marrow_light"),
    ):
        head, said = fibula_like_head(plane, target, light)
        assert said == code and not head.any()
    head, said = fibula_like_head(plane, target, LIGHT)
    assert said == "abstain_no_projected_fibula" and not head.any()
    target[5, 5] = True
    assert fibula_like_head(plane, target, LIGHT)[1] == "identified"
    nans = plane.copy()
    nans[:] = np.nan
    assert fibula_like_head(nans, target, LIGHT)[1] == (
        "abstain_no_marrow_like_body_at_the_fibula"
    )
    with pytest.raises(ValueError, match="head_inputs_must_share"):
        fibula_like_head(plane, target[:-1], LIGHT)


def test_two_bodies_holding_exactly_as_many_places_are_not_told_apart() -> None:
    plane = np.full((20, 40), 100.0)
    plane[3:13, 3:13] = LIGHT
    plane[3:9, 25:35] = LIGHT  # a smaller body: only the held places count
    target = np.zeros(plane.shape, dtype=bool)
    target[5, 5] = target[5, 6] = target[5, 27] = target[5, 28] = True
    head, code = fibula_like_head(plane, target, LIGHT)
    assert code == "abstain_tied_head_bodies" and not head.any()
    target[6, 6] = True
    head, code = fibula_like_head(plane, target, LIGHT)
    assert code == "identified" and head[3:13, 3:13].all()


def test_the_head_areas_say_empty_unreadable_and_measured_apart() -> None:
    head = np.zeros((10, 10), dtype=bool)
    head[:4, :5] = True
    pitch = np.asarray([0.5, 2.0])
    assert head_area_mm2(head, "identified", pitch) == 20.0
    assert (
        head_area_mm2(head, "abstain_no_marrow_like_body_at_the_fibula", pitch) == 0.0
    )
    for code in (
        "abstain_no_projected_fibula",
        "abstain_no_fibula_marrow_light",
        "abstain_tied_head_bodies",
    ):
        assert np.isnan(head_area_mm2(head, code, pitch))
    assert np.isnan(head_area_mm2(head, "identified", np.asarray([0.0, 1.0])))
    assert np.isnan(head_area_mm2(head, "identified", np.asarray([np.nan, 1.0])))


def test_tied_sizes_and_empty_sizes_have_no_largest() -> None:
    assert unique_largest(np.asarray([3, 9, 4])) == 1
    assert unique_largest(np.asarray([9, 9, 4])) is None
    assert unique_largest(np.asarray([], dtype=int)) is None
    assert unique_largest(np.asarray([5])) == 0


def test_the_twins_marrow_light_is_read_where_the_twin_has_a_say() -> None:
    twin = np.asarray([[10.0, np.nan], [30.0, 20.0]])
    assert twin_marrow_light(twin, np.ones((2, 2), bool)) == 20.0
    assert np.isnan(
        twin_marrow_light(twin, np.asarray([[False, True], [False, False]]))
    )
    assert np.isnan(twin_marrow_light(twin, np.zeros((2, 2), bool)))


# ---- the slice: the walk outward from the fibula's main slice ----------------------------

ORIGINS = np.asarray([[3.0 * z, 0.0, 0.0] for z in range(10)])
NORMAL = np.asarray([1.0, 0.0, 0.0])
FIBULA = np.asarray([[15.0, 20.0, -110.0], [15.0, 22.0, -112.0]])  # slice 5's plane


class Heads:
    """A stand-in for the per-slice head area, that remembers which slices were asked about."""

    def __init__(self, areas):
        self.areas, self.asked = areas, []

    def __call__(self, z):
        self.asked.append(z)
        return self.areas.get(z, 0.0)


def walk(heads, knee="R", fibula=FIBULA, origins=ORIGINS, thick=None, normal=NORMAL):
    thick = [3.0] * len(origins) if thick is None else thick
    return lateral_to_the_head(fibula, origins, normal, thick, knee, heads)


def test_the_walk_goes_outward_while_the_head_is_a_disc_and_reads_lazily() -> None:
    heads = Heads({5: 300.0, 4: 200.0, 3: 100.0, 2: 80.0, 1: 70.0, 0: 400.0})
    chosen, areas, status, code = walk(heads)  # a right knee's outer side is toward -x
    assert (chosen, code) == (1, "identified")
    assert heads.asked == [5, 4, 3, 2, 1]  # no slice past the answer, none inward
    assert areas[1:6].tolist() == [70.0, 80.0, 100.0, 200.0, 300.0]
    # slices the walk never reached are unread, NaN, which is not a measured zero
    assert np.isnan(areas[[0, 6, 7, 8, 9]]).all()
    assert status.tolist() == [0, 2, 1, 1, 1, 1, 0, 0, 0, 0]
    assert status[1] == HEAD_SLICE_STATUS["head_no_longer_a_disc"]
    assert areas.dtype == np.float64 and status.dtype == np.int8


def test_a_left_knee_and_a_reversed_stack_walk_the_same_physical_way() -> None:
    mirrored = {5: 300.0, 6: 200.0, 7: 70.0}
    chosen, _, _, code = walk(Heads(mirrored), knee="L")
    assert (chosen, code) == (7, "identified")
    backwards = ORIGINS[::-1].copy()  # slices numbered from the other side
    chosen, _, _, code = walk(
        Heads({4: 300.0, 5: 200.0, 6: 70.0}), "R", origins=backwards
    )
    assert (chosen, code) == (6, "identified")  # the fibula is now slice 4; outer is up
    # the knee's outer side, not the numbering, decides: the right knee read from either end
    assert walk(Heads({5: 300.0, 6: 70.0}), "L")[0] == 6


def test_the_disc_boundary_is_inclusive_of_a_disc_and_exclusive_of_less() -> None:
    at = Heads({5: 300.0, 4: BONE_DISC_MM2, 3: 0.0})
    assert walk(at)[0] == 3  # exactly a disc is still a disc
    below = Heads({5: 300.0, 4: float(np.nextafter(BONE_DISC_MM2, 0.0)), 3: 300.0})
    assert walk(below)[0] == 4
    assert round(BONE_DISC_MM2, 2) == 78.54


@pytest.mark.parametrize("at", [5, 4])
def test_an_unreadable_head_stops_the_walk_instead_of_being_taken_for_empty(at) -> None:
    heads = Heads({5: 300.0, 4: 200.0, 3: 100.0, at: float("nan")})
    chosen, areas, status, code = walk(heads)
    assert chosen is None and code == "abstain_head_unreadable_on_the_way"
    assert status[at] == HEAD_SLICE_STATUS["head_unreadable"]
    assert heads.asked[-1] == at and np.isnan(areas[at])
    assert np.isnan(areas[at - 1 : 4]).all() or at == 5
    negative = Heads({5: 300.0, 4: -1.0})
    assert walk(negative)[3] == "abstain_head_unreadable_on_the_way"


def test_a_fibula_that_is_not_a_disc_where_it_is_found_names_no_slice() -> None:
    chosen, areas, _, code = walk(Heads({5: 50.0}))
    assert (
        chosen is None and code == "abstain_the_fibula_is_not_a_disc_on_its_main_slice"
    )
    assert areas[5] == 50.0 and np.isnan(areas[4])


def test_a_series_that_ends_before_the_head_does_names_no_slice() -> None:
    heads = Heads({z: 300.0 for z in range(10)})
    chosen, areas, status, code = walk(heads)
    assert chosen is None and code == "abstain_the_series_ends_before_the_head_does"
    assert heads.asked == [5, 4, 3, 2, 1, 0]
    assert (status[:6] == HEAD_SLICE_STATUS["head_still_a_disc"]).all()
    assert np.isnan(areas[6:]).all()


def test_missing_or_unusable_geometry_asks_no_slice_anything() -> None:
    cases = [
        ({"knee": ""}, "abstain_header_names_no_knee"),
        ({"knee": "X"}, "abstain_header_names_no_knee"),
        ({"fibula": np.empty((0, 3))}, "abstain_no_fibula"),
        ({"fibula": np.empty(0)}, "abstain_no_fibula"),
        ({"fibula": FIBULA + [60.0, 0, 0]}, "abstain_no_slice_holds_the_fibula"),
        ({"origins": ORIGINS[:1]}, "abstain_the_series_has_one_slice"),
        (
            {"normal": np.asarray([0.0, 1.0, 0.0])},
            "abstain_slices_do_not_run_side_to_side",
        ),
        ({"thick": [3.0] * 9 + [None]}, "abstain_no_slice_thickness"),
        ({"thick": [3.0] * 9 + [0.0]}, "abstain_no_slice_thickness"),
        ({"thick": [3.0] * 9 + [float("nan")]}, "abstain_no_slice_thickness"),
        (
            {"origins": np.tile(ORIGINS[:1], (10, 1)), "fibula": FIBULA - [15.0, 0, 0]},
            "abstain_slices_do_not_run_side_to_side",
        ),
    ]
    for kw, expected in cases:
        heads = Heads({5: 300.0})
        if "origins" in kw and len(kw["origins"]) == 1:
            kw = dict(kw, thick=[3.0])
        chosen, areas, status, code = walk(heads, **kw)
        assert chosen is None and code == expected, kw
        assert heads.asked == [] and np.isnan(areas).all() and not status.any()


def test_malformed_geometry_is_refused_loudly() -> None:
    heads = Heads({})
    with pytest.raises(ValueError, match="invalid_fibula_places"):
        walk(heads, fibula=np.asarray([[1.0, 2.0]]))
    with pytest.raises(ValueError, match="invalid_fibula_places"):
        walk(heads, fibula=np.asarray([[np.nan, 0.0, 0.0]]))
    with pytest.raises(ValueError, match="invalid_slice_origins"):
        walk(heads, origins=ORIGINS[:, :2])
    with pytest.raises(ValueError, match="invalid_slice_origins"):
        walk(heads, origins=np.where(ORIGINS == 3.0, np.nan, ORIGINS))
    with pytest.raises(ValueError, match="thicknesses_must_match"):
        walk(heads, thick=[3.0])
    with pytest.raises(ValueError, match="invalid_series_normal"):
        walk(heads, normal=np.zeros(3))
    assert heads.asked == []


# ---- carrying the fibula's places onto another slice ------------------------------------


def frame_at(x: float) -> PlaneFrame:
    # columns toward the back (+y), rows down (-z), 1 mm pixels: a sagittal slice at x
    return PlaneFrame.from_dicom([x, 0.0, 0.0], [0, 1, 0, 0, 0, -1], (1.0, 1.0))


def test_places_project_onto_a_slice_however_far_off_its_plane() -> None:
    frame = frame_at(0.0)
    far = np.asarray([[40.0, 10.0, -5.0], [40.0, 12.0, -6.0]])
    held = projected_places(far, frame, (20, 30))
    expected = np.zeros((20, 30), dtype=bool)
    expected[5, 10] = expected[6, 12] = True
    assert np.array_equal(held, expected)
    # the slab keeps only what lies within half the thickness: this is a different operation
    assert not places_on_slice(far, frame, (20, 30), 3.0).any()
    near = np.asarray([[1.0, 10.0, -5.0], [40.0, 12.0, -6.0]])
    only_near = places_on_slice(near, frame, (20, 30), 3.0)
    assert only_near.sum() == 1 and only_near[5, 10]


def test_places_outside_the_picture_or_none_hold_no_pixel() -> None:
    frame = frame_at(0.0)
    outside = np.asarray([[0.0, 100.0, -5.0], [0.0, 3.0, 50.0], [0.0, -4.0, -5.0]])
    assert not projected_places(outside, frame, (20, 30)).any()
    for none in (np.empty((0, 3)), np.empty(0), []):
        held = projected_places(np.asarray(none), frame, (20, 30))
        assert held.shape == (20, 30) and not held.any()
    with pytest.raises(ValueError):
        projected_places(np.asarray([[np.nan, 0.0, 0.0]]), frame, (20, 30))
    with pytest.raises(ValueError):
        projected_places(np.asarray([[1.0, 2.0]]), frame, (20, 30))


# ---- the registry -----------------------------------------------------------------------


def test_the_tendon_has_its_code_and_a_placeholder_decision_on_every_slice() -> None:
    assert OBJECT_CODES["biceps_femoris_tendon"] == 40
    assert len(set(OBJECT_CODES.values())) == len(OBJECT_CODES)
    assert "biceps_femoris_tendon" in SLICE_PARTS


# ---- the chain, on a synthetic series: the walk, then the rule --------------------------


def test_the_walk_and_the_rule_agree_through_real_frames() -> None:
    """Five sagittal slices, the head's body shrinking outward (toward -x for a right knee): the
    fibula's places are carried onto each by projection, each head's area is read once, the walk
    stops where it is less than a disc, and the rule names the cord on that slice."""
    sizes = {4: (105, 121, 20, 38), 3: (105, 117, 22, 34), 2: (105, 115, 23, 33)}
    sizes |= {1: (105, 113, 24, 32), 0: (105, 113, 24, 32)}
    planes, twins = {}, {}
    for z, head_box in sizes.items():
        planes[z], twins[z], target = scene(head=head_box, cord=(50, 105, 24, 32))
    frames = {z: frame_at(3.0 * z) for z in sizes}
    rows, cols = np.nonzero(target)
    fibula = np.column_stack((np.full(len(rows), 12.0), cols, -rows)).astype(float)
    origins = np.asarray([frames[z].origin_lps for z in range(5)])
    made = {}

    def head_area_at(z):
        shape = planes[z].shape
        mask, code = fibula_like_head(
            planes[z], projected_places(fibula, frames[z], shape), LIGHT
        )
        made[z] = mask
        return head_area_mm2(mask, code, np.asarray(frames[z].spacing_rc))

    chosen, areas, _, code = lateral_to_the_head(
        fibula, origins, frames[4].normal(), [3.0] * 5, "R", head_area_at
    )
    assert (chosen, code) == (1, "identified")
    assert areas[1:].tolist() == [64.0, 100.0, 144.0, 288.0] and np.isnan(areas[0])
    assert sorted(made) == [
        1,
        2,
        3,
        4,
    ]  # the head of the slice chosen was made once, in the walk
    mask, readings, said = proximal_biceps_on_slice(
        planes[1], twins[1], frames[1].basis_lps, LIGHT, TWIN_LIGHT, made[1]
    )
    assert said == "identified"
    expected = np.zeros(mask.shape, dtype=bool)
    expected[50:103, 24:32] = True
    assert np.array_equal(mask, expected)
    assert float(readings["piece_reach_to_head_mm"][0]) == pytest.approx(3.0)
