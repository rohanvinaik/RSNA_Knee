from types import SimpleNamespace
from typing import cast

import numpy as np
import pytest

from knee.collapse.physical import PlaneFrame
from knee.objects.assignments import (
    OBJECT_CODES,
    Peak,
    PlaneAssignment,
    enclosed_darkness,
    popliteal_lumens,
)
from scripts import run_interiors


def lumen_scene():
    depth = np.zeros((30, 32), dtype=np.float64)
    depth[4:10, 4:12] = 7.0
    depth[17:24, 18:27] = 5.0
    depth[12, 15] = 100.0  # a deeper speck without a 2 mm body
    depth[10:17, 29:32] = 9.0  # strong component that crosses the corridor edge
    corridor = np.zeros(depth.shape, dtype=bool)
    corridor[2:27, 2:29] = True
    rows, _ = np.indices(depth.shape)
    return depth, corridor, rows.astype(float)


def test_enclosed_darkness_measures_a_uint16_lumen_without_subtraction_wrap():
    plane = np.full((13, 13), 80, dtype=np.uint16)
    plane[3:10, 3:10] = 120
    plane[4:9, 4:9] = 20

    depth = enclosed_darkness(plane)

    assert depth.dtype == np.float64
    assert np.all(depth[4:9, 4:9] == 100.0)
    assert not depth[0].any()
    assert not depth[:, 0].any()


def test_enclosed_darkness_handles_uniform_and_empty_planes_and_rejects_bad_inputs():
    assert not enclosed_darkness(np.full((4, 7), 42, dtype=np.uint16)).any()
    empty = enclosed_darkness(np.empty((0, 7), dtype=np.float32))
    assert empty.shape == (0, 7)
    assert empty.dtype == np.float64
    with pytest.raises(ValueError, match="plane_must_be_2d"):
        enclosed_darkness(np.zeros(3))
    with pytest.raises(ValueError, match="plane_must_be_finite"):
        enclosed_darkness(np.array([[0.0, np.nan]]))


def test_lumens_keep_two_strong_complete_components_and_order_by_back_position():
    depth, corridor, back = lumen_scene()

    artery, vein, labels, code = popliteal_lumens(
        depth, corridor, back, np.array((1.0, 1.0))
    )

    assert code == "identified"
    assert labels.dtype == np.int32
    assert np.array_equal(
        artery, np.pad(np.ones((6, 8), dtype=bool), ((4, 20), (4, 20)))
    )
    assert np.array_equal(vein, np.pad(np.ones((7, 9), dtype=bool), ((17, 6), (18, 5))))
    assert labels[12, 15] != 0  # all measured closed interiors remain represented
    assert labels[13, 30] != 0
    assert not artery[12, 15] and not vein[12, 15]
    assert not artery[:, 29:].any() and not vein[:, 29:].any()

    reverse_artery, reverse_vein, _, reverse_code = popliteal_lumens(
        depth, corridor, -back, np.array((1.0, 1.0))
    )
    assert reverse_code == "identified"
    assert np.array_equal(reverse_artery, vein)
    assert np.array_equal(reverse_vein, artery)


def test_lumen_body_requirement_uses_physical_spacing():
    depth = np.zeros((20, 24), dtype=np.float64)
    depth[3:8, 3:11] = 4.0
    depth[12:17, 13:21] = 3.0
    corridor = np.ones(depth.shape, dtype=bool)
    rows, _ = np.indices(depth.shape)
    back = rows.astype(float)

    _, _, _, ordinary_spacing = popliteal_lumens(
        depth, corridor, back, np.array((1.0, 1.0))
    )
    _, _, _, compressed_spacing = popliteal_lumens(
        depth, corridor, back, np.array((0.3, 1.0))
    )

    assert ordinary_spacing == "identified"
    assert compressed_spacing == "abstain_no_lumen_pair"


def test_equal_posterior_position_abstains_without_selecting_a_pair():
    depth, corridor, _ = lumen_scene()
    back = np.zeros(depth.shape, dtype=np.float64)

    artery, vein, labels, code = popliteal_lumens(
        depth, corridor, back, np.array((1.0, 1.0))
    )

    assert code == "abstain_ambiguous_vessel_order"
    assert not artery.any() and not vein.any()
    assert labels.any()


def head_scene(knee="R", reverse_side=False):
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
    inner = cols.astype(float) - 15.0
    if reverse_side:
        inner = -inner
    objects = np.zeros(labels.shape, dtype=np.int8)
    objects[15, 8] = OBJECT_CODES["skin"]
    assignment = PlaneAssignment(
        objects, {}, peaks, None, None, in_plane=(True, True, False)
    )
    own = cast(
        run_interiors.Measured,
        SimpleNamespace(
            series=SimpleNamespace(
                row=SimpleNamespace(fat_suppression="1"),
                slice_thickness_mm=(3.0,),
            ),
            record={
                "slice_index": 0,
                "assignments": {"knee": knee, "codes": {}},
            },
            arrays={
                "acquired_plane": np.ones(labels.shape),
                "b1_labels": labels,
                "a1_objects": objects,
            },
            assignment=assignment,
            frame=PlaneFrame(
                np.zeros(3),
                np.array([[0.0, 1.0], [1.0, 0.0], [0.0, 0.0]]),
                (1.0, 1.0),
            ),
        ),
    )
    carried = run_interiors.Carried(
        bone, np.zeros_like(bone), rows.astype(float), inner
    )
    return own, carried


@pytest.mark.parametrize("reverse_side", [False, True])
def test_driver_builds_the_same_between_heads_corridor_under_side_reversal(
    monkeypatch, reverse_side
):
    own, carried = head_scene(reverse_side=reverse_side)
    observed = {}

    monkeypatch.setattr(run_interiors, "carry_onto", lambda *args: carried)
    monkeypatch.setattr(
        run_interiors, "enclosed_darkness", lambda plane: np.zeros_like(plane)
    )

    def select(depth, corridor, back, spacing):
        observed["corridor"] = corridor.copy()
        return (
            np.zeros(corridor.shape, dtype=bool),
            np.zeros(corridor.shape, dtype=bool),
            np.zeros(corridor.shape, dtype=np.int32),
            "abstain_no_lumen_pair",
        )

    monkeypatch.setattr(run_interiors, "popliteal_lumens", select)
    run_interiors.name_the_back_of_the_knee(
        own,
        run_interiors.Leg(
            np.empty((0, 3)), np.empty((0, 3)), None, None, np.empty((0, 3))
        ),
    )

    assert observed["corridor"][8:15, 10:20].all()
    assert not observed["corridor"][:, :8].any()
    assert not observed["corridor"][:, 23:].any()
    assert not observed["corridor"][:8].any()
    assert not observed["corridor"][18:].any()


def test_driver_saves_layered_lumens_and_preserves_prior_object_pixels(monkeypatch):
    own, carried = head_scene()
    monkeypatch.setattr(run_interiors, "carry_onto", lambda *args: carried)
    artery = np.zeros((20, 30), dtype=bool)
    vein = np.zeros_like(artery)
    artery[10, 14] = True
    vein[11, 14] = True
    monkeypatch.setattr(
        run_interiors,
        "popliteal_lumens",
        lambda depth, corridor, back, spacing: (
            artery,
            vein,
            np.zeros((20, 30), dtype=np.int32),
            "identified",
        ),
    )
    original = own.arrays["a1_objects"].copy()

    head_codes = run_interiors.name_the_back_of_the_knee(
        own,
        run_interiors.Leg(
            np.empty((0, 3)), np.empty((0, 3)), None, None, np.empty((0, 3))
        ),
    )

    assert set(head_codes) == {"medial_gastrocnemius", "lateral_gastrocnemius"}
    assert own.record["assignments"]["codes"]["popliteal_artery"] == "identified"
    assert own.record["assignments"]["codes"]["popliteal_vein"] == "identified"
    assert np.array_equal(own.arrays["a2_popliteal_artery"], artery)
    assert np.array_equal(own.arrays["a2_popliteal_vein"], vein)
    assert own.arrays["a1_objects"][15, 8] == OBJECT_CODES["skin"]
    assert own.assignment.objects[15, 8] == original[15, 8]
