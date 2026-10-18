"""Where a selected slice lies along its stack in physical normalized terms: a reversed stack aligns with its
forward twin, unequal spacing is carried by the places and not the index, a left knee's medial side is the right
knee's mirrored, and what cannot be placed is None with its reason."""

import numpy as np

from scripts import slice_positions as sp


def stack(places, axis=0, in_plane=((0.0, 0.0), (5.0, 5.0))):
    """Tile centres (slices, 2, 2, 3): each slice's places along `axis`, the tiles spread in the plane."""
    centres = np.zeros((len(places), 2, 2, 3))
    other = [a for a in range(3) if a != axis]
    for k, p in enumerate(places):
        for i in range(2):
            for j in range(2):
                centres[k, i, j, axis] = p
                centres[k, i, j, other[0]] = in_plane[i][0]
                centres[k, i, j, other[1]] = in_plane[j][1]
    return centres


def row(g, plane, slice_index, knee="R", code="identified"):
    o = {
        "series_uid": "s",
        "view": [plane, "0", "0"],
        "slices": [slice_index],
        "code": code,
        "count": 10,
        "off_plane_mm": 0.0,
        "support": "a1_objects",
        "artifact": "study/s-fibula.npz",
        "row": None,
        "label": 10,
    }
    return sp.observation_row(
        "study",
        "fibula",
        "native",
        "resolved",
        "a1_objects",
        o,
        dict(g, knee=knee, middle=2),
    )


def test_a_reversed_stack_gives_the_same_physical_position_as_its_forward_twin():
    forward = sp.stack_geometry(stack([-30.0, -20.0, -10.0, 0.0, 10.0]))
    backward = sp.stack_geometry(stack([10.0, 0.0, -10.0, -20.0, -30.0]))
    assert not forward["reversed"] and backward["reversed"]
    # slice 1 of the forward stack is slice 3 of the reversed one: the same place, so the same t
    a = row(forward, "Sagittal", 1)
    b = row(backward, "Sagittal", 3)
    assert a["t_patient_axis"] == b["t_patient_axis"] == 0.25
    assert a["q_mm"] == b["q_mm"] == 10.0
    # while the raw index fractions differ: that is the thing a raw index gets wrong
    assert a["t_by_index"] == 0.25 and b["t_by_index"] == 0.75


def test_unequal_spacing_is_carried_by_the_places_not_the_index():
    g = sp.stack_geometry(stack([0.0, 1.0, 2.0, 10.0, 20.0]))
    assert g["extent"] == 20.0 and g["gap_spread"] == 10.0
    middle = row(g, "Coronal", 2)
    assert middle["t_patient_axis"] == 0.1 and middle["t_by_index"] == 0.5
    assert row(g, "Coronal", 3)["t_patient_axis"] == 0.5


def test_the_axis_is_the_one_the_stack_runs_along_and_a_label_that_disagrees_is_said():
    axial = sp.stack_geometry(stack([0.0, 3.0, 6.0], axis=2))
    assert sp.AXES[axial["axis"]] == "z_toward_head"
    wrong = row(
        axial, "Sagittal", 1
    )  # a sagittal-labelled series whose stack runs along z
    assert (
        wrong["axis"] == "z_toward_head" and wrong["axis_matches_plane_label"] is False
    )


def test_a_left_knees_medial_side_is_the_right_knees_mirrored_and_no_knee_is_unknown():
    g = sp.stack_geometry(stack([-20.0, -10.0, 0.0, 10.0, 20.0]))
    right = row(
        g, "Sagittal", 4, knee="R"
    )  # toward the patient's left = medial for a right knee
    left = row(g, "Sagittal", 4, knee="L")
    assert right["t_side_lateral0_medial1"] == 1.0
    assert left["t_side_lateral0_medial1"] == 0.0
    none = row(g, "Sagittal", 4, knee=None)
    assert (
        none["t_side_lateral0_medial1"] is None
        and none["side_reason"] == "header_names_no_knee"
    )
    assert none["t_patient_axis"] == 1.0  # the patient-axis position is still known
    assert row(g, "Coronal", 4)["t_side_lateral0_medial1"] is None


def test_what_cannot_be_placed_is_none_with_its_reason_never_zero():
    assert sp.stack_geometry(stack([5.0]))["reason"] == "single_slice_stack"
    assert sp.stack_geometry(stack([5.0, 5.0, 5.0]))["reason"] == "zero_stack_step"
    holes = stack([0.0, 1.0, 2.0])
    holes[1] = np.nan
    assert sp.stack_geometry(holes)["reason"] == "slice_without_finite_tiles"
    unknown = row({"reason": "no_squint_centres", "n": None}, "Coronal", 1)
    assert "t_patient_axis" not in unknown
    assert unknown["position_unavailable_reason"] == "no_squint_centres"
    g = sp.stack_geometry(stack([0.0, 1.0, 2.0]))
    off_the_stack = row(g, "Coronal", 7)  # a slice index the stack does not have
    assert off_the_stack["t_patient_axis"] is None and off_the_stack["q_mm"] is None


def test_the_role_says_how_the_slice_came_to_be_the_one():
    base = {
        "object": "femur",
        "series_uid": "s",
        "provenance": "native",
        "kind": "resolved",
    }
    middle = dict(base, support="a1_objects", artifact="study/s.npz")
    own = dict(base, support="a1_objects", artifact="study/s-fibula.npz")
    pointed = dict(base, support="a3_femur_plane_region", artifact="study/s.npz")
    assert sp.role_of(middle) == "middle_bootstrap"
    assert sp.role_of(own) == "own_slice_rule"
    assert sp.role_of(pointed) == "profile_pointed_plane"
    assert sp.role_of(dict(middle, object="air")) == "context_middle_naming"
    assert (
        sp.role_of(dict(middle, provenance="projected", kind="target"))
        == "projected_target"
    )
    assert (
        sp.role_of(dict(middle, kind="reading", support="a3_femur_profile_area_mm2"))
        == "profile_run"
    )
