"""The bones' collapse: marrow body through depth, pointed planes, identity by carried places."""

from types import SimpleNamespace
from typing import Any, cast

import numpy as np

from knee.collapse.bones import (
    AMBIGUOUS,
    BODY_ELSEWHERE,
    IDENTIFIED,
    TIE,
    marrow_body,
    name_territory,
    section_extent,
    tiles_touched,
)
from knee.collapse.physical import PlaneFrame, physical_squint
from knee.collapse.profile import positive_runs, run_maxima
from knee.objects import assignments as A
from knee.objects.interiors import InteriorRegions
from knee.telemetry import computing, recording
from scripts import run_interiors as run

LIGHT = 400.0
LEVEL = A.LIKE_THE_TIBIA
BLOCK = (2.0, 2.0)  # a 2 mm block; the disc rule wants 5 mm from the edge


def window(rows=24, cols=24):
    return np.full((rows, cols), 0.3 * LIGHT)


def body_of(median, own, other=None, open_edge=None):
    other = np.zeros(median.shape, bool) if other is None else other
    edge = np.zeros(median.shape, bool) if open_edge is None else open_edge
    return marrow_body(median, BLOCK, LIGHT, LEVEL, own, other, edge)


def test_a_plateau_keeps_every_tied_slice_and_every_run():
    area = np.array([0, 5.0, 5.0, 0, 3.0, 0])
    runs = positive_runs(area)
    got = run_maxima(area, runs)
    assert runs == [(1, 3), (4, 5)] and [m.tolist() for m in got] == [[1, 2], [4]]


def test_separated_condyles_are_one_bones_body_summed():
    m = window()
    m[2:10, 2:10] = LIGHT
    m[2:10, 14:22] = LIGHT
    own = m == LIGHT
    got = body_of(m, own)
    assert got.pieces == 2 and not got.merged
    assert got.area_mm2 == 2 * 64 * 4.0


def test_a_coarse_merge_of_the_two_bones_does_not_decide_identity():
    m = window()
    m[2:12, 2:10] = LIGHT  # femur
    m[14:20, 2:10] = LIGHT  # tibia
    m[12:14, 5:7] = LIGHT  # a bridge joins them
    femur = np.zeros(m.shape, bool)
    femur[2:12, 2:10] = True
    tibia = np.zeros(m.shape, bool)
    tibia[14:20, 2:10] = True
    got = body_of(m, femur, tibia)
    assert got.merged
    assert not (got.body & tibia).any()  # the tibia's blocks are never the femur's
    # one lens territory over both bones names neither
    labels = np.ones((8, 8), int)
    a = np.zeros((8, 8), bool)
    a[:3] = True
    assert (
        name_territory(labels, np.ones((8, 8), bool), a, ~a).code
        == "territory_holding_most"
    )  # a merged territory is not the bone
    a[:5] = True
    b = np.zeros((8, 8), bool)
    b[3:] = True
    avail = np.ones((8, 8), bool)
    assert name_territory(labels, avail, a, b).code == AMBIGUOUS
    assert name_territory(labels, avail, b, a).code == AMBIGUOUS


def test_identity_needs_the_marrow_body_in_the_named_territory():
    labels = np.zeros((8, 8), int)
    labels[:4], labels[4:] = 1, 2
    avail = np.ones((8, 8), bool)
    places = labels == 1
    body = labels == 2
    assert name_territory(labels, avail, places, ~places).code == IDENTIFIED
    assert name_territory(labels, avail, places, ~places, body).code == BODY_ELSEWHERE


def test_territories_holding_equally_are_a_tie_none_chosen():
    labels = np.zeros((4, 4), int)
    labels[:, :2], labels[:, 2:] = 1, 2
    places = np.zeros((4, 4), bool)
    places[0, 1:3] = True
    got = name_territory(labels, np.ones((4, 4), bool), places, np.zeros((4, 4), bool))
    assert got.code == TIE and not got.region.any() and got.tied == (1, 2)


def test_unseen_places_are_unavailable_not_absent():
    labels = np.ones((4, 4), int)
    places = np.ones((4, 4), bool)
    got = name_territory(labels, np.zeros((4, 4), bool), places, ~places)
    assert got.code == "unavailable"


def test_section_ends_are_observed_clipped_or_unresolved():
    up = np.tile(np.arange(10.0)[::-1][:, None], (1, 10))  # row 0 is the top
    mask = np.zeros((10, 10), bool)
    mask[0:5, 3:6] = True  # reaches the picture's top edge
    avail = np.ones((10, 10), bool)
    got = section_extent(mask, up, avail, 0.5)
    assert got is not None
    low, high, low_end, high_end = got
    assert (low, high) == (5.0, 9.0) and high_end == "clipped_by_the_scan"
    assert low_end == "observed"
    avail[5, 4] = False  # a place never seen under the section
    again = section_extent(mask, up, avail, 0.5)
    assert again is not None and again[2] == "unresolved"
    assert section_extent(np.zeros((10, 10), bool), up, avail, 0.5) is None


def test_a_reversed_stack_gives_the_same_physical_envelopes():
    status = np.array([2, 2, 2, 1], np.int8)
    offsets = np.array([0.0, 3.0, 6.0, 9.0])
    thick = np.full(4, 3.0)
    a, _, spans = run.describe_runs([(0, 3)], status, offsets, thick, True)
    b, _, rspans = run.describe_runs([(1, 4)], status[::-1], offsets[::-1], thick, True)
    assert spans[0].tolist() == rspans[0].tolist() == [-1.5, 7.5]
    assert b[0]["slices"] == [1, 3]
    assert a[0]["ends"] == ["clipped_by_the_scan", "observed_end"]


# -- the profile through the real function --------------------------------------------------------
PITCH = 1.5


def frame() -> PlaneFrame:
    return PlaneFrame(
        np.zeros(3), np.array([[0.0, 1.5], [1.5, 0.0], [0.0, 0.0]]), (PITCH, PITCH)
    )


class Plain:
    def __init__(self, planes):
        self.row = SimpleNamespace(series_uid="s", fat_suppression="0")
        self.volume = planes


def stack_for(planes, unseen=()):
    sq = [physical_squint(p, (PITCH, PITCH), 10.0) for p in planes]
    minimum = np.stack([s.minimum.copy() for s in sq])
    maximum = np.stack([s.maximum.copy() for s in sq])
    for i, j in unseen:
        minimum[:, i, j] = maximum[:, i, j] = np.nan
    return SimpleNamespace(
        minimum=minimum,
        maximum=maximum,
        median=np.stack([s.median for s in sq]),
        coverage=np.stack([s.coverage for s in sq]),
        bounds_rc=sq[0].bounds_rc,
        tile_shape_rc=sq[0].tile_shape_rc,
    )


def profile(monkeypatch, planes, light=LIGHT, unseen=()):
    f = frame()
    monkeypatch.setattr(run, "plane_frame", lambda s, z: f)
    monkeypatch.setattr(
        run,
        "seen_native",
        lambda s, z, stage="x": (
            np.asarray(planes[z], float),
            np.zeros(planes[z].shape, bool),
        ),
    )
    shape = planes[0].shape
    foot = np.zeros(shape, bool)
    foot[2:12, 2:12] = True
    monkeypatch.setattr(
        run,
        "bone_footprint",
        lambda s, z, f, _sh, places, key: foot if places[0, 0] == 1 else foot & False,
    )
    with computing(), recording() as led:
        got = run.bone_profile(
            cast(Any, Plain(planes)),
            cast(Any, stack_for(planes, unseen)),
            np.ones((1, 3)),
            np.zeros((1, 3)),
            light,
            "bones",
        )
    return got, led


def test_a_nonfinite_or_nonpositive_anchor_is_unreadable_never_absent(monkeypatch):
    planes = [np.full((30, 30), 0.2 * LIGHT)] * 2
    for light in (float("nan"), float("inf") * 0.0, 0.0, -5.0):
        got, _ = profile(monkeypatch, planes, light)
        assert (got.status == A.FIBULA_POINTER_STATUS["unreadable"]).all()
        assert np.isnan(got.area_mm2).all() and not got.fine


def test_a_level_nothing_can_reach_is_absent_and_reads_nothing_finer(monkeypatch):
    got, led = profile(monkeypatch, [np.full((30, 30), 0.2 * LIGHT)])
    assert got.status[0] == A.FIBULA_POINTER_STATUS["none"] and got.area_mm2[0] == 0.0
    assert not got.fine
    assert (
        sum(
            e.counts.get("planes", 0)
            for e in led.events()
            if e.name == "bones.tile_exclusions"
        )
        == 1
    )


def test_partial_coarse_coverage_is_unknown_not_absent(monkeypatch):
    planes = [np.full((30, 30), 0.2 * LIGHT)]
    tiles = stack_for(planes).bounds_rc.shape[:2]
    every = [(i, j) for i in range(tiles[0]) for j in range(tiles[1])]
    got, _ = profile(monkeypatch, planes, unseen=every)
    assert got.status[0] == A.FIBULA_POINTER_STATUS["unreadable"]
    assert np.isnan(got.area_mm2[0])


def test_a_marrow_body_is_read_finely_and_kept_at_its_own_resolution(monkeypatch):
    plane = np.full((30, 30), 0.2 * LIGHT)
    plane[3:12, 3:12] = LIGHT
    got, _ = profile(monkeypatch, [plane, plane])
    assert (got.status == A.FIBULA_POINTER_STATUS["body"]).all()
    assert got.area_mm2[0] > 0 and len(got.fine) == 2
    assert tiles_touched(np.ones((30, 30), bool), stack_for([plane]).bounds_rc).all()


# -- the pointed planes through the real read_bone ------------------------------------------------
def world(monkeypatch, labels):
    calls: list[int] = []
    f = frame()
    shape = labels.shape

    def lens(plane, *_, available):
        calls.append(1)
        z = np.zeros(plane.shape)
        return InteriorRegions(
            "measured", z.astype(bool), available, z, z.astype(np.int32), labels
        )

    monkeypatch.setattr(run, "plane_frame", lambda s, z: f)
    monkeypatch.setattr(run, "finite_of", lambda s: np.ones((3, *shape), bool))
    monkeypatch.setattr(run, "interior_regions", lens)
    planes = [np.full(shape, LIGHT) for _ in range(3)]
    series = SimpleNamespace(
        row=SimpleNamespace(series_uid="w", fat_suppression="0"),
        volume=planes,
        geometry=SimpleNamespace(
            position=[np.array([0.0, 0.0, 3.0 * k]) for k in range(3)]
        ),
        slice_thickness_mm=(3.0, 3.0, 3.0),
    )
    objects = np.zeros(shape, np.int8)
    objects[0:4] = A.OBJECT_CODES["femur"]
    objects[5:9] = A.OBJECT_CODES["tibia"]
    own = SimpleNamespace(
        series=series,
        record={
            "slice_index": 0,
            "background_split": 1.0,
            "series_uid": "w",
            "view": ["S", "0", "0"],
            "assignments": {"femur": 1, "tibia": 2},
        },
        arrays={
            "a1_objects": objects,
            "acquired_plane": planes[0],
            "b1_available": np.ones(shape, bool),
        },
        stack=SimpleNamespace(code="present"),
        frame=f,
    )
    return own, calls


def fake_profile(depth=3, point=1):
    area = np.zeros(depth)
    area[point] = 100.0
    return run.BoneProfile(
        np.full(depth, 2, np.int8),
        area,
        np.ones(depth, np.int32),
        np.zeros(depth, bool),
        np.zeros((depth, 1, 1), bool),
        np.zeros((depth, 1, 1), bool),
        np.zeros((depth, 1, 1), bool),
        np.full((depth, 4), -1, np.int32),
        np.full((depth, 2), np.nan),
        np.full((depth, 2), -1, np.int32),
        (),
        LIGHT,
    )


def test_two_bones_pointing_to_one_plane_read_its_lens_once_and_failures_keep_readings(
    monkeypatch,
):
    labels = np.zeros((12, 12), np.int32)  # no territory anywhere under the places
    own, calls = world(monkeypatch, labels)
    monkeypatch.setattr(run, "bone_profile", lambda *a: fake_profile())
    f = frame()
    pts = f.to_patient(np.argwhere(np.ones((12, 12), bool)).astype(float))
    with computing(), recording():
        femur = run.read_bone(cast(Any, own), "femur", pts, pts[:0])
        tibia = run.read_bone(cast(Any, own), "tibia", pts, pts[:0])
        assert isinstance(femur, run.BoneRead) and isinstance(tibia, run.BoneRead)
        run.keep_bone_planes(cast(Any, own), {"femur": femur, "tibia": tibia})
    assert len(calls) == 1  # one plane, one lens, for both bones
    assert (
        femur.planes[0].code == "no_territory_under_the_places"
        and femur.outcome == "unresolved"
    )
    assert (
        "a3_femur_profile_area_mm2" in own.arrays
        and own.arrays["a3_bone_plane_labels"].shape[0] == 1
    )
    assert own.arrays["a3_femur_plane_outcome"].tolist() == [
        -1 + 1 + 4
    ]  # index of the code
    assert femur.record["pointed_planes"][0]["position_mm"] in (3.0, -3.0)


def test_a_series_without_the_bone_or_with_fat_suppression_is_named_not_skipped(
    monkeypatch,
):
    own, _ = world(monkeypatch, np.zeros((12, 12), np.int32))
    pts = np.zeros((1, 3))
    own.arrays["a1_objects"][:] = 0
    assert (
        run.read_bone(cast(Any, own), "femur", pts, pts)
        == "bone_not_named_on_the_middle_slice"
    )
    own.arrays["a1_objects"][0:4] = A.OBJECT_CODES["femur"]
    own.series.row.fat_suppression = "1"
    assert (
        run.read_bone(cast(Any, own), "femur", pts, pts)
        == "fat_suppressed_not_profiled"
    )
