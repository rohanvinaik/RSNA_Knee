"""The lateral head uses the existing condyle/head rules on the opposite physical side."""

from types import SimpleNamespace
from typing import cast

import numpy as np
import pytest

from knee.collapse.physical import PlaneFrame
from knee.objects.assignments import (
    OBJECT_CODES,
    Peak,
    PlaneAssignment,
    gastrocnemius_head,
    inner_condyle,
)
from scripts import run_interiors


def head_scene():
    """Two condyles with one posterior muscle territory behind each."""
    labels = np.zeros((20, 30), dtype=np.int32)
    labels[5:10, 4:12] = 2
    labels[5:10, 18:26] = 3
    labels[12:19, 4:12] = 4
    labels[12:19, 18:26] = 5
    peaks = (
        Peak(3, 16.0, (7, 22), 0.0),
        Peak(2, 15.0, (7, 8), 0.0),
        Peak(4, 12.0, (15, 8), 0.0),
        Peak(5, 10.0, (15, 22), 0.0),
    )
    rows, cols = np.indices(labels.shape)
    bone = np.isin(labels, (2, 3))
    return labels, peaks, bone, rows.astype(float), cols.astype(float) - 15.0


def test_the_existing_rule_on_the_opposite_side_resolves_the_lateral_head():
    labels, peaks, bone, back, inner = head_scene()
    medial = inner_condyle(peaks, labels, bone, inner)
    lateral = inner_condyle(peaks, labels, bone, -inner)
    assert medial is not None and medial.territory == 3
    assert lateral is not None and lateral.territory == 2
    assert np.array_equal(
        gastrocnemius_head(peaks, labels, bone, medial, back, inner), labels == 5
    )
    assert np.array_equal(
        gastrocnemius_head(peaks, labels, bone, lateral, back, -inner), labels == 4
    )


def test_a_lateral_condyle_requires_carried_bone_on_the_outer_side():
    labels, peaks, _, _, inner = head_scene()
    assert inner_condyle(peaks, labels, labels == 3, -inner) is None


def test_no_head_is_named_when_no_outer_peak_lies_behind_the_outer_condyle():
    labels, peaks, bone, back, inner = head_scene()
    condyle = inner_condyle(peaks, labels, bone, -inner)
    assert condyle is not None
    without_outer_head = tuple(peak for peak in peaks if peak.territory != 4)
    assert not gastrocnemius_head(
        without_outer_head, labels, bone, condyle, back, -inner
    ).any()
    assert not gastrocnemius_head(peaks, labels, bone, condyle, -back, -inner).any()


def test_negating_the_physical_inner_axis_swaps_the_selected_head():
    labels, peaks, bone, back, inner = head_scene()
    other_knee_inner = -inner
    opposite_condyle = inner_condyle(peaks, labels, bone, -other_knee_inner)
    assert opposite_condyle is not None and opposite_condyle.territory == 3
    assert np.array_equal(
        gastrocnemius_head(
            peaks, labels, bone, opposite_condyle, back, -other_knee_inner
        ),
        labels == 5,
    )


def measured_scene(knee="R", outer_condyle=True, outer_head=True):
    labels, peaks, bone, back, toward_left = head_scene()
    if not outer_condyle:
        bone[labels == 2] = False
    if not outer_head:
        peaks = tuple(peak for peak in peaks if peak.territory != 4)
    objects = np.zeros(labels.shape, dtype=np.int8)
    objects[15, 8] = OBJECT_CODES["skin"]  # a pre-existing name must survive
    assignment = PlaneAssignment(
        objects,
        {},
        peaks,
        None,
        None,
        in_plane=(True, True, False),
    )
    frame = PlaneFrame(
        np.zeros(3), np.array([[0.0, 1.0], [1.0, 0.0], [0.0, 0.0]]), (1.0, 1.0)
    )
    # This boundary needs the recorded values below, not an on-disk study decoder.
    own = cast(
        run_interiors.Measured,
        SimpleNamespace(
            series=SimpleNamespace(
                row=SimpleNamespace(fat_suppression="1"), slice_thickness_mm=(3.0,)
            ),
            record={"slice_index": 0, "assignments": {"knee": knee, "codes": {}}},
            arrays={
                "acquired_plane": np.ones(labels.shape),
                "b1_labels": labels,
                "a1_objects": objects,
            },
            assignment=assignment,
            frame=frame,
        ),
    )
    carried = run_interiors.Carried(bone, np.zeros_like(bone), back, toward_left)
    return own, carried


@pytest.mark.parametrize("knee", ["R", "L"])
def test_driver_carries_once_and_names_each_head_without_overwriting_objects(
    monkeypatch, knee
):
    own, carried = measured_scene(knee)
    original = own.assignment.objects.copy()
    calls = []

    def carry_once(*args):
        calls.append(args)
        return carried

    monkeypatch.setattr(run_interiors, "carry_onto", carry_once)
    leg = run_interiors.Leg(np.empty((0, 3)), np.empty((0, 3)), None, None)
    codes = run_interiors.name_the_back_of_the_knee(own, leg)
    assert codes == {
        "medial_gastrocnemius": "identified",
        "lateral_gastrocnemius": "identified",
    }
    assert len(calls) == 1
    assigned = own.record["assignments"]
    assert assigned["medial_gastrocnemius"] == (5 if knee == "R" else 4)
    assert assigned["lateral_gastrocnemius"] == (4 if knee == "R" else 5)
    labels = own.arrays["b1_labels"]
    objects = own.arrays["a1_objects"]
    expected_medial = labels == assigned["medial_gastrocnemius"]
    expected_lateral = labels == assigned["lateral_gastrocnemius"]
    assert np.array_equal(
        objects == OBJECT_CODES["medial_gastrocnemius"],
        expected_medial & (original == 0),
    )
    assert np.array_equal(
        objects == OBJECT_CODES["lateral_gastrocnemius"],
        expected_lateral & (original == 0),
    )
    assert objects[15, 8] == OBJECT_CODES["skin"]
    assert np.array_equal(own.assignment.objects, original)


def test_driver_without_a_leg_abstains_for_both_heads():
    own, _ = measured_scene()
    codes = run_interiors.name_the_back_of_the_knee(own, None)
    assert codes == {
        "medial_gastrocnemius": "abstain_no_bone_carried",
        "lateral_gastrocnemius": "abstain_no_bone_carried",
    }
    assert own.record["assignments"]["medial_gastrocnemius"] is None
    assert own.record["assignments"]["lateral_gastrocnemius"] is None
    assert not np.isin(own.arrays["a1_objects"], (20, 30)).any()


@pytest.mark.parametrize(
    "outer_condyle, outer_head, expected",
    [
        (False, True, "abstain_no_outer_condyle"),
        (True, False, "abstain_no_body_behind_the_outer_condyle"),
    ],
)
def test_driver_names_the_lateral_missing_part_without_changing_the_medial_result(
    monkeypatch, outer_condyle, outer_head, expected
):
    own, carried = measured_scene(outer_condyle=outer_condyle, outer_head=outer_head)
    monkeypatch.setattr(run_interiors, "carry_onto", lambda *args: carried)
    leg = run_interiors.Leg(np.empty((0, 3)), np.empty((0, 3)), None, None)
    codes = run_interiors.name_the_back_of_the_knee(own, leg)
    assert codes["medial_gastrocnemius"] == "identified"
    assert codes["lateral_gastrocnemius"] == expected
    assert not (own.arrays["a1_objects"] == OBJECT_CODES["lateral_gastrocnemius"]).any()
