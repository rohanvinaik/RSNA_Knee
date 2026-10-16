"""Intent tests for the sartorius on a middle axial: local lightness, muscle-grey bodies, and the
selection by relation to the gracilis's projected places."""

import numpy as np
import pytest

from knee.collapse.physical import PlaneFrame
from knee.objects.assignments import (
    GRACILIS_REACH_MM,
    MUSCLE_GREY,
    OBJECT_CODES,
    SARTORIUS_BODY_STATUS,
    SLICE_PARTS,
    Measures,
    assign_plane,
    local_lightness,
    muscle_grey_bodies,
    sartorius_on_slice,
    window_pixels,
)
from knee.objects.interiors import InteriorRegions

SHAPE = (80, 80)
OFF_PLANE_MM = 20.0


def frame_for(spacing=(1.0, 1.0), transposed=False):
    """Rows toward the back, columns toward the patient's left (a right knee's inner side)."""
    sr, sc = spacing
    basis = np.array([[0.0, sc], [sr, 0.0], [0.0, 0.0]])
    if transposed:
        basis = basis[:, ::-1]
        spacing = spacing[::-1]
    return PlaneFrame(np.zeros(3), basis, spacing)


def block(rows, cols, shape=SHAPE):
    mask = np.zeros(shape, dtype=bool)
    mask[rows, cols] = True
    return mask


def places_of(mask, frame):
    """A mask's places in the scanner's millimetres, put OFF_PLANE_MM away from the slice."""
    lps = frame.to_patient(np.argwhere(mask).astype(float))
    return lps + OFF_PLANE_MM * frame.normal()


def scene(sheet=(slice(30, 50), slice(28, 34))):
    """A flat 100 plane, a 200 sheet (ratio about 2) medial to and in front of a target."""
    plane = np.full(SHAPE, 100.0)
    plane[sheet] = 200.0
    target = block(slice(50, 56), slice(18, 21))
    return plane, target


def run(plane, target, knee="R", frame=None, low=None, unseen=None, **kw):
    frame = frame_for() if frame is None else frame
    none = np.zeros(plane.shape, dtype=bool)
    return sartorius_on_slice(
        plane,
        none if low is None else low,
        none if unseen is None else unseen,
        places_of(target, frame),
        frame,
        knee,
        **kw,
    )


def test_names_the_whole_grey_sheet_medial_to_and_in_front_of_the_projected_target():
    plane, target = scene()
    mask, readings, code = run(plane, target)

    assert code == "identified"
    sheet = block(slice(30, 50), slice(28, 34))
    # the sampling median rounds a rectangle's corners; the body is the sheet, whole
    assert not (mask & ~sheet).any() and mask.sum() >= 0.8 * sheet.sum()
    assert mask[31:49, 29:33].all()
    assert np.array_equal(
        readings["gracilis_target"], target
    )  # a location, not the mask
    assert float(readings["gracilis_source_separation_mm"]) == pytest.approx(
        OFF_PLANE_MM
    )
    ratio = readings["lightness"][mask]
    assert np.all((ratio >= MUSCLE_GREY[0]) & (ratio < MUSCLE_GREY[1]))
    status = readings["body_status"]
    assert (
        status[readings["grey_bodies"][mask][0] - 1]
        == SARTORIUS_BODY_STATUS["selected"]
    )
    for name, value in readings.items():
        assert isinstance(value, np.ndarray) and value.dtype != object, name


def test_each_relation_is_needed_inner_side_front_and_reach():
    far_side = scene(
        (slice(30, 50), slice(6, 12))
    )  # toward the outer side of the target
    behind = scene((slice(58, 78), slice(28, 34)))  # behind the target
    too_far = scene(
        (slice(30, 50), slice(60, 66))
    )  # medial and in front, but 40 mm away
    for plane, target in (far_side, behind):
        mask, readings, code = run(plane, target)
        assert code == (
            "abstain_no_grey_body_medial_to_and_in_front_of_the_gracilis_target"
        )
        assert not mask.any() and readings["eligible_ids"].size == 0
    mask, readings, code = run(*too_far)
    assert code == "abstain_no_grey_body_within_reach_of_the_gracilis_target"
    assert not mask.any()
    assert readings["eligible_reach_mm"].min() > GRACILIS_REACH_MM
    assert SARTORIUS_BODY_STATUS["beyond_reach"] in readings["body_status"]


def test_a_left_knee_takes_the_other_side_as_inner():
    plane, target = scene()
    assert run(plane, target, knee="R")[2] == "identified"
    assert run(plane, target, knee="L")[2] == (
        "abstain_no_grey_body_medial_to_and_in_front_of_the_gracilis_target"
    )
    # the same picture with the sheet on the target's outer side is the inner one for a left knee
    plane, target = scene((slice(30, 50), slice(6, 12)))
    assert run(plane, target, knee="L")[2] == "identified"


def test_names_every_missing_prerequisite_and_measures_nothing_it_did_not_reach():
    plane, target = scene()
    frame = frame_for()
    none = np.zeros(SHAPE, dtype=bool)
    refused = {
        "abstain_header_names_no_knee": run(plane, target, knee=""),
        "abstain_no_gracilis_source": sartorius_on_slice(
            plane, none, none, np.empty((0, 3)), frame, "R"
        ),
        "abstain_gracilis_projects_outside_the_picture": sartorius_on_slice(
            plane, none, none, places_of(target, frame) + [0.0, 500.0, 0.0], frame, "R"
        ),
    }
    for expect, (mask, _, code) in refused.items():
        assert code == expect and not mask.any() and mask.shape == SHAPE
    assert refused["abstain_header_names_no_knee"][1] == {}
    assert (
        "lightness" not in refused["abstain_gracilis_projects_outside_the_picture"][1]
    )
    assert (
        "gracilis_target" in refused["abstain_gracilis_projects_outside_the_picture"][1]
    )


def test_flat_contrast_and_zero_light_give_no_body_not_a_false_one():
    flat = np.full(SHAPE, 150.0)
    target = block(slice(50, 56), slice(18, 21))
    mask, readings, code = run(flat, target)
    assert code == "abstain_no_soft_tissue_grey_body" and not mask.any()
    assert np.allclose(readings["lightness"][np.isfinite(readings["lightness"])], 1.0)

    zero = np.zeros(SHAPE)  # zero reference everywhere: NaN, not infinity or a body
    mask, readings, code = run(zero, target)
    assert code == "abstain_no_local_contrast" and not mask.any()
    assert np.isnan(readings["lightness"]).all()
    assert "grey_bodies" not in readings


def test_unseen_and_low_places_have_no_reading_and_make_no_body():
    plane, target = scene()
    plane[30:50, 28:34] = np.nan  # the sheet was never seen here
    unseen = ~np.isfinite(plane)
    mask, readings, code = run(plane, target, unseen=unseen)
    assert code == "abstain_no_soft_tissue_grey_body" and not mask.any()
    assert np.isnan(readings["lightness"][unseen]).all()
    assert not (readings["grey_bodies"][unseen] > 0).any()

    plane, target = scene()
    low = np.zeros(SHAPE, dtype=bool)
    low[30:50, 28:34] = True  # lens-low: not a muscle-grey body however light it is
    mask, readings, code = run(plane, target, low=low)
    assert not mask.any() and np.isnan(readings["lightness"][low]).all()


def test_low_places_are_left_out_of_every_surround_not_counted_as_dark():
    plane = np.full(SHAPE, 100.0)
    low = np.zeros(SHAPE, dtype=bool)
    low[:, :40] = True
    plane[low] = 0.0
    lightness, smooth, surround = local_lightness(plane, low, np.array([1.0, 1.0]))
    # beside the low half the surround is the seen half's 100, not a median dragged down by zeros
    assert surround[40, 45] == pytest.approx(100.0)
    assert np.isnan(smooth[low]).all() and np.isnan(lightness[low]).all()
    # a place whose whole window is excluded has no surround and no ratio
    assert np.isnan(surround[40, 5]) and np.isnan(lightness[40, 5])


def test_whole_bodies_are_eight_connected():
    plane = np.full(SHAPE, 100.0)
    for rows, cols in ((slice(30, 34), slice(28, 32)), (slice(34, 38), slice(32, 36))):
        plane[rows, cols] = 200.0  # two blocks meeting at a corner: one body
    labels = muscle_grey_bodies(
        local_lightness(plane, np.zeros(SHAPE, bool), np.ones(2))[0]
    )
    assert labels[31, 30] == labels[36, 34] > 0
    target = block(slice(42, 47), slice(22, 26))
    mask, _, code = run(plane, target)
    assert code == "identified" and mask[31, 30] and mask[36, 34]


def test_the_largest_whole_body_wins_over_a_smaller_one_in_reach():
    plane = np.full(SHAPE, 100.0)
    plane[40:49, 32:41] = 200.0  # the big one
    plane[40:45, 24:29] = (
        200.0  # a smaller separate one, also medial, in front, in reach
    )
    target = block(slice(52, 57), slice(22, 26))
    mask, readings, code = run(plane, target)
    assert code == "identified" and mask[44, 36] and not mask[42, 26]
    assert (readings["body_status"] == SARTORIUS_BODY_STATUS["within_reach"]).sum() == 1
    assert (readings["body_status"] == SARTORIUS_BODY_STATUS["selected"]).sum() == 1


def test_disconnected_bodies_of_exactly_equal_size_abstain():
    plane = np.full(SHAPE, 100.0)
    plane[38:43, 24:29] = 200.0
    plane[45:50, 24:29] = 200.0  # a twin, two rows apart
    target = block(slice(51, 56), slice(22, 26))
    mask, readings, code = run(plane, target)
    assert code == "abstain_tied_largest_bodies" and not mask.any()
    assert (readings["body_status"] == SARTORIUS_BODY_STATUS["within_reach"]).sum() == 2


def test_narrow_things_are_rubbed_away_by_the_sampling_lens():
    plane = np.full(SHAPE, 100.0)
    plane[30:50, 30:32] = 200.0  # two pixels across: below the 3-pixel sampling lens
    target = block(slice(50, 56), slice(18, 21))
    mask, _, code = run(plane, target)
    assert code == "abstain_no_soft_tissue_grey_body" and not mask.any()
    bright = np.full(SHAPE, 100.0)
    bright[30:50, 28:34] = 500.0  # a ratio of 5: white, not muscle
    assert run(bright, target)[2] == "abstain_no_soft_tissue_grey_body"


def test_window_and_reach_follow_physical_spacing_not_pixels():
    assert window_pixels(np.array([1.0, 1.0]), 20.0) == (21, 21)
    assert window_pixels(np.array([2.0, 0.5]), 20.0) == (11, 41)
    assert window_pixels(np.array([20.0, 40.0]), 20.0) == (1, 1)
    with pytest.raises(ValueError):
        window_pixels(np.array([0.0, 1.0]), 20.0)
    # nine rows apart is 9 mm at 1 mm a row and 18 mm at 2 mm a row
    for spacing, code in (
        ((1.0, 1.0), "identified"),
        ((2.0, 1.0), "abstain_no_grey_body_within_reach_of_the_gracilis_target"),
    ):
        plane = np.full(SHAPE, 100.0)
        plane[38:44, 22:30] = 200.0  # 6 rows by 8 columns
        target = block(slice(53, 56), slice(21, 24))
        got = run(plane, target, frame=frame_for(spacing))
        reach = got[1]["eligible_reach_mm"]
        assert got[2] == code, reach


def test_follows_transposed_native_axes():
    plane, target = scene()
    straight = run(plane, target)
    swapped = run(plane.T, target.T, frame=frame_for(transposed=True))
    assert straight[2] == swapped[2] == "identified"
    assert np.array_equal(swapped[0], straight[0].T)


def test_shared_measures_give_the_same_answer_and_inputs_are_unchanged():
    plane, target = scene()
    frame = frame_for()
    none = np.zeros(SHAPE, dtype=bool)
    lps = places_of(target, frame)
    before = [a.copy() for a in (plane, none, lps)]
    alone = sartorius_on_slice(plane, none, none, lps, frame, "R")
    shared = sartorius_on_slice(
        plane, none, none, lps, frame, "R", Measures(None, plane, frame.basis_lps)
    )
    assert np.array_equal(alone[0], shared[0]) and alone[2] == shared[2] == "identified"
    assert np.array_equal(
        alone[1]["target_distance_mm"], shared[1]["target_distance_mm"]
    )
    for first, second in zip(before, (plane, none, lps), strict=True):
        assert np.array_equal(first, second)


def test_mismatched_inputs_are_refused():
    plane, target = scene()
    with pytest.raises(ValueError):
        sartorius_on_slice(
            plane,
            np.zeros((3, 3), bool),
            np.zeros(SHAPE, bool),
            places_of(target, frame_for()),
            frame_for(),
            "R",
        )


def test_has_its_code_and_a_placeholder_on_every_slice_and_keeps_the_earlier_codes():
    assert OBJECT_CODES["sartorius"] == 42
    assert (
        OBJECT_CODES["gracilis"] == 41 and OBJECT_CODES["biceps_femoris_tendon"] == 40
    )
    assert len(set(OBJECT_CODES.values())) == len(OBJECT_CODES)
    assert SLICE_PARTS.count("sartorius") == 1

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
    assert assigned.codes["sartorius"] == "abstain_requires_the_gracilis_source"
    assert not (assigned.objects == OBJECT_CODES["sartorius"]).any()
