"""The shared coarse depth and the body section selected by sparse carried seeds."""

from __future__ import annotations

from types import SimpleNamespace
from typing import cast

import numpy as np
import pytest

from knee.collapse import relative as rel
from knee.collapse.coarse_section import (
    EMPTY,
    NOT_READ,
    SECTION,
    SEEDS_UNSEEN,
    SHARED,
    body_extent_mm,
    coarse_depth,
    coarse_section,
    key_slices,
)
from knee.collapse.physical import PlaneFrame
from knee.collapse.profile import BlockReading, block_medians
from knee.collapse.study_map import StudyMap
from scripts import run_interiors as run


def enclosed(dark: bool) -> np.ndarray:
    image = np.full((40, 40), 100.0)
    rr, cc = np.mgrid[:40, :40]
    radius = np.hypot(rr - 20, cc - 20)
    image[radius <= 8] = 30.0 if dark else 170.0
    image[(radius > 8) & (radius <= 10)] = 5.0
    if dark:
        image[(radius > 10) & (radius <= 12)] = 200.0
    return image


@pytest.mark.parametrize("dark", [True, False])
def test_coarse_depth_reads_either_marrow_polarity_and_ignores_unseen(dark):
    image = enclosed(dark)
    image[0, 0] = np.nan
    image[0, 1] = 0.0  # excluded margin is supplied by the block reader in production
    depth = coarse_depth(image, dark)
    assert depth.shape == image.shape
    assert np.isfinite(depth[20, 20]) and depth[20, 20] > 0
    assert np.isnan(coarse_depth(np.full((3, 3), np.nan), dark)).all()


def test_sparse_seed_any_overlap_recovers_and_fills_the_whole_coarse_section():
    depth = coarse_depth(enclosed(True), True)
    seeds = np.zeros(depth.shape, dtype=bool)
    seeds[20, 11] = (
        True  # one location block is enough; ownership is not a majority vote
    )
    got = coarse_section(depth, seeds, 4.0)
    assert got.status == SECTION and got.body is not None
    assert got.body[20, 20] and not got.body[0, 0]
    assert got.body.sum() > 30 * seeds.sum()
    assert got.area_mm2 == got.body.sum() * 4.0


def test_unseen_and_margin_values_cannot_change_a_coarse_depth_reading():
    first = np.arange(64, dtype=float).reshape(8, 8)
    hidden = np.zeros(first.shape, dtype=bool)
    hidden[0, 0] = True
    second = first.copy()
    second[0, 0] = -1e9
    a = block_medians(first, hidden, (1.0, 1.0), 2.0)
    b = block_medians(second, hidden, (1.0, 1.0), 2.0)
    assert np.isnan(a.median[0, 0]) and np.isnan(b.median[0, 0])
    np.testing.assert_array_equal(a.median, b.median)
    np.testing.assert_array_equal(
        coarse_depth(a.median, True), coarse_depth(b.median, True)
    )


def test_other_bone_seed_inside_the_same_section_is_not_attributed():
    depth = coarse_depth(enclosed(True), True)
    femur = np.zeros(depth.shape, dtype=bool)
    tibia = np.zeros(depth.shape, dtype=bool)
    femur[20, 11] = True
    tibia[20, 20] = True
    got = coarse_section(depth, femur, 1.0, {"tibia": tibia})
    assert got.status == SHARED and got.body is None


def test_unknown_empty_and_unseen_are_distinct_from_absence():
    empty = np.full((4, 4), np.nan)
    marks = np.zeros((4, 4), dtype=bool)
    assert coarse_section(empty, marks, 1.0).status == NOT_READ
    marks[2, 2] = True
    assert coarse_section(empty, marks, 1.0).status == SEEDS_UNSEEN
    assert coarse_section(np.zeros((4, 4)), marks, 1.0).status == EMPTY


def test_key_plane_ties_and_mediolateral_extent_use_physical_block_corners():
    assert key_slices(np.array([np.nan, 4.0, 4.0, 0.0])) == (1, 2)
    frame = PlaneFrame(
        np.zeros(3), np.array([[0.0, 1.0], [1.0, 0.0], [0.0, 0.0]]), (2.0, 2.0)
    )
    reading = BlockReading(np.ones((3, 4)), (1, 1), (2.0, 2.0), (0, 3, 0, 4))
    body = np.zeros((3, 4), dtype=bool)
    body[0:3, 1:3] = True
    assert body_extent_mm(body, reading, frame, (1.0, 0.0, 0.0)) == 2.0


def test_malformed_grid_inputs_are_refused_by_name():
    with pytest.raises(ValueError, match="median_must_be_2d"):
        coarse_depth(np.ones(4), True)
    with pytest.raises(ValueError, match="seeds_must_share_the_block_grid"):
        coarse_section(np.ones((2, 2)), np.ones((3, 3), dtype=bool), 1.0)


def test_axial_scout_skips_slices_without_an_allowed_bone_seed(monkeypatch):
    shape = (60, 60)
    volume = np.stack([enclosed(True), enclosed(True)])
    line = np.zeros(shape, dtype=bool)
    line[25:36, 30] = True
    empty = np.zeros(shape, dtype=bool)
    monkeypatch.setattr(
        run,
        "plane_frame",
        lambda series, z: PlaneFrame(
            np.array([0.0, 0.0, 10.0 * z]),
            np.array([[0.0, 1.0], [1.0, 0.0], [0.0, 0.0]]),
            (1.0, 1.0),
        ),
    )
    monkeypatch.setattr(
        run,
        "leg_on",
        lambda leg, series, z, frame, shape, thick: (
            (line, line) if z == 0 else (line, empty)
        ),
    )
    monkeypatch.setattr(
        run,
        "block_medians",
        lambda *args, **kwargs: (_ for _ in ()).throw(
            AssertionError("unseeded plane read")
        ),
    )
    series = SimpleNamespace(
        row=SimpleNamespace(series_uid="coarse-no-active-test", fat_suppression="1"),
        volume=volume,
        slice_thickness_mm=[3.0, 3.0],
    )
    own = SimpleNamespace(
        series=series,
        arrays={"acquired_plane": volume[0]},
        record={"view": ["Axial", "1", "1"]},
    )
    leg = SimpleNamespace(
        femur_lps=np.array([[0.0, 0.0, 1.0]]),
        tibia_lps=np.array([[0.0, 0.0, 20.0]]),
    )
    said = run.axial_bone_planes(
        StudyMap(knee="R"), cast(run.Measured, own), cast(run.Leg, leg)
    )
    assert said["femur"]["statuses"] == {run.AXIAL_OVERLAP: 2}
    assert said["tibia"]["statuses"] == {run.AXIAL_OVERLAP: 1}
    assert own.arrays["a4_axial_femur_identity_excluded"].tolist() == [True, True]


def test_axial_extent_uses_the_matching_read_slice_after_unreadable_geometry(
    monkeypatch,
):
    shape = (40, 40)
    volume = np.stack([enclosed(True), enclosed(True)])
    line = np.zeros(shape, dtype=bool)
    line[15:26, 20] = True
    empty = np.zeros(shape, dtype=bool)
    frame = PlaneFrame(
        np.zeros(3), np.array([[0.0, 1.0], [1.0, 0.0], [0.0, 0.0]]), (1.0, 1.0)
    )
    monkeypatch.setattr(
        run, "plane_frame", lambda series, z: "unreadable" if z == 0 else frame
    )
    monkeypatch.setattr(
        run,
        "leg_on",
        lambda leg, series, z, frame, shape, thick: (
            (empty, empty) if z == 0 else (line, empty)
        ),
    )
    monkeypatch.setattr(
        run,
        "map_plane",
        lambda own, bone, z, reason, provenance: rel.plane_of_frame(
            bone,
            "axial",
            series_uid="coarse-skipped-frame-test",
            slice=z,
            frame=frame,
            precision_mm=1.0,
        ),
    )
    block_calls = []
    depth_calls = []
    make_blocks = run.block_medians
    make_depth = run.coarse_depth
    monkeypatch.setattr(
        run,
        "block_medians",
        lambda *args, **kwargs: block_calls.append(1) or make_blocks(*args, **kwargs),
    )
    monkeypatch.setattr(
        run,
        "coarse_depth",
        lambda *args, **kwargs: depth_calls.append(1) or make_depth(*args, **kwargs),
    )
    series = SimpleNamespace(
        row=SimpleNamespace(
            series_uid="coarse-skipped-frame-test", fat_suppression="1"
        ),
        volume=volume,
        slice_thickness_mm=[3.0, 3.0],
    )
    own = SimpleNamespace(
        series=series,
        arrays={"acquired_plane": volume[1]},
        record={"view": ["Axial", "1", "1"]},
    )
    leg = SimpleNamespace(
        femur_lps=np.array([[0.0, 0.0, 20.0]]),
        tibia_lps=np.array([[0.0, 0.0, -20.0]]),
    )
    smap = StudyMap(knee="R")
    with run.computing():
        said = run.axial_bone_planes(smap, cast(run.Measured, own), cast(run.Leg, leg))
        run.axial_bone_planes(
            StudyMap(knee="R"), cast(run.Measured, own), cast(run.Leg, leg)
        )
    assert said["femur"]["key_slices"] == [1]
    assert smap.selected("femur", "axial").slice == 1
    assert block_calls == [1] and depth_calls == [1]
