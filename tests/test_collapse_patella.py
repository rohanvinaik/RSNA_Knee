"""The patella's collapse: the relation corridor, the profile through it, pointed planes, failures."""

from types import SimpleNamespace
from typing import Any, cast

import numpy as np

from knee.collapse.patella import femur_landmarks, in_front_of_the_femur
from knee.collapse.physical import PlaneFrame, physical_squint
from knee.collapse.profile import positive_runs, run_maxima
from knee.objects import assignments as A
from knee.telemetry import computing, recording
from scripts import run_interiors as run

LIGHT = 100.0
PITCH = 1.5


def test_the_femurs_landmarks_ignore_nonfinite_places_and_empty_is_none():
    pts = np.array([[0, -50.0, 10], [0, -40, 5], [0, np.nan, -99], [0, -60, np.inf]])
    assert femur_landmarks(pts) == (-50.0, 5.0)
    assert femur_landmarks(np.empty((0, 3))) is None
    assert femur_landmarks(np.full((2, 3), np.nan)) is None


def test_in_front_of_the_femur_is_the_established_relation_with_a_tile_margin():
    pts = np.array(
        [[0, -60.0, 30], [0, -40, 30], [0, -60, 70], [0, -60, 3], [0, np.nan, 30]]
    )
    got = in_front_of_the_femur(pts, -50.0, 5.0)
    assert got.tolist() == [True, False, False, False, False]
    wide = in_front_of_the_femur(pts, -50.0, 5.0, margin_mm=5.0)
    assert wide.tolist() == [
        True,
        False,
        False,
        True,
        False,
    ]  # z 3 is within half a tile


# -- the profile through the real bone_profile, with a relation's corridor ---------------------
def frame() -> PlaneFrame:
    return PlaneFrame(
        np.zeros(3), np.array([[0.0, 1.5], [1.5, 0.0], [0.0, 0.0]]), (PITCH, PITCH)
    )


class Plain:
    def __init__(self, planes):
        self.row = SimpleNamespace(series_uid="s", fat_suppression="1")
        self.volume = planes


def stack_for(planes):
    sq = [physical_squint(p, (PITCH, PITCH), 10.0) for p in planes]
    return SimpleNamespace(
        minimum=np.stack([s.minimum for s in sq]),
        maximum=np.stack([s.maximum for s in sq]),
        median=np.stack([s.median for s in sq]),
        coverage=np.stack([s.coverage for s in sq]),
        bounds_rc=sq[0].bounds_rc,
        tile_shape_rc=sq[0].tile_shape_rc,
    )


def profile(monkeypatch, planes, light=LIGHT):
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
    monkeypatch.setattr(
        run, "bone_footprint", lambda *a: np.zeros(planes[0].shape, bool)
    )
    corridor = np.zeros(planes[0].shape, bool)
    corridor[2:14, 2:14] = True
    with computing(), recording() as led:
        got = run.bone_profile(
            cast(Any, Plain(planes)),
            cast(Any, stack_for(planes)),
            np.empty((0, 3)),
            np.zeros((1, 3)),
            light,
            "patella",
            lambda z, _fr, shape: corridor,
            A.LIKE_THE_FEMUR,
        )
    return got, led


def body_plane(outside=False):
    plane = np.full((30, 30), 0.1 * LIGHT)
    plane[3:12, 3:12] = LIGHT  # in the corridor
    if outside:
        plane[18:28, 18:28] = (
            LIGHT  # the femur's own marrow: same light, beyond the corridor
        )
    return plane


def test_marrow_like_blocks_beyond_the_corridor_never_join_the_body(monkeypatch):
    a, _ = profile(monkeypatch, [body_plane()])
    b, _ = profile(monkeypatch, [body_plane(outside=True)])
    assert a.area_mm2[0] > 0 and a.area_mm2[0] == b.area_mm2[0]


def test_a_plateau_keeps_every_tied_plane_and_the_ledger_names_the_patella(monkeypatch):
    got, led = profile(
        monkeypatch, [body_plane(), body_plane(), np.full((30, 30), 5.0)]
    )
    runs = positive_runs(got.area_mm2)
    assert runs == [(0, 2)] and run_maxima(got.area_mm2, runs)[0].tolist() == [0, 1]
    assert got.status[2] == A.FIBULA_POINTER_STATUS["none"] and got.area_mm2[2] == 0.0
    names = {e.name for e in led.events()}
    assert "patella.cheap_readings" in names and "bones.cheap_readings" not in names


def test_a_nonfinite_or_nonpositive_anchor_is_unreadable_never_absent(monkeypatch):
    for light in (float("nan"), 0.0, -3.0):
        got, _ = profile(monkeypatch, [body_plane()] * 2, light)
        assert (got.status == A.FIBULA_POINTER_STATUS["unreadable"]).all()
        assert np.isnan(got.area_mm2).all()


def test_unseen_tiles_are_unknown_not_absent(monkeypatch):
    plane = np.full((30, 30), np.nan)
    got, _ = profile(monkeypatch, [plane])
    assert got.status[0] == A.FIBULA_POINTER_STATUS["unreadable"]
    assert np.isnan(got.area_mm2[0])


# -- the refusals and the failure paths ---------------------------------------------------------
def view(fat="1", in_plane=(False, True, True), femur=True):
    objects = np.zeros((12, 12), np.int8)
    if femur:
        objects[0:4] = A.OBJECT_CODES["femur"]
    return SimpleNamespace(
        series=SimpleNamespace(
            row=SimpleNamespace(
                series_uid="w", fat_suppression=fat, fluid_sensitive="1"
            ),
            volume=[np.full((12, 12), LIGHT)] * 3,
        ),
        record={
            "series_uid": "w",
            "slice_index": 0,
            "background_split": 1.0,
            "assignments": {"femur": 1 if femur else None, "codes": {}},
            "view": ["S", fat, fat],
        },
        arrays={"a1_objects": objects, "acquired_plane": np.full((12, 12), LIGHT)},
        assignment=SimpleNamespace(in_plane=in_plane),
        stack=SimpleNamespace(code="present"),
        frame=frame(),
    )


def test_the_native_rules_own_refusals_name_why_no_series_is_skipped_silently():
    pts = np.zeros((2, 3))
    got = lambda own: run.read_patella(cast(Any, own), None, pts, pts)
    assert got(view(fat="0")) == "abstain_fat_as_bright_as_marrow"
    assert got(view(in_plane=(True, False, True))) == (
        "abstain_front_to_back_runs_through_the_plane"
    )
    assert got(view(femur=False)) == "abstain_no_femur"


def test_a_plane_whose_geometry_cannot_be_read_is_a_code_not_a_crash(monkeypatch):
    monkeypatch.setattr(run, "plane_frame", lambda s, z: "geometry_unreadable")
    got = run.patella_plane(
        cast(Any, view()), 1, np.zeros((1, 3)), np.zeros((1, 3)), ("a", "b"), None
    )
    assert got.code == run.UNREADABLE_GEOMETRY and got.objects is None


def test_a_plane_with_no_femur_keeps_its_lens_readings_and_names_the_reason(
    monkeypatch,
):
    shape = (12, 12)
    f = frame()
    labels = np.zeros(shape, np.int32)
    labels[3:6, 3:6] = 1
    monkeypatch.setattr(run, "plane_frame", lambda s, z: f)
    monkeypatch.setattr(
        run,
        "lens_of",
        lambda *a, **k: (
            None,
            SimpleNamespace(labels=labels, available=np.ones(shape, bool)),
            {},
        ),
    )
    field = SimpleNamespace(
        objects=np.zeros(shape, np.int8),
        peaks=(),
        in_plane=(False, True, True),
        leg=np.ones(shape, bool),
    )
    monkeypatch.setattr(run, "field_of", lambda *a: field)
    monkeypatch.setattr(run, "bone_footprint", lambda *a: np.zeros(shape, bool))
    with computing(), recording():
        got = run.patella_plane(
            cast(Any, view()), 1, np.zeros((1, 3)), np.zeros((1, 3)), ("a", "b"), None
        )
    assert got.code == "abstain_no_femur" and got.labels is not None
    assert (
        got.objects is not None and not (got.objects == A.OBJECT_CODES["patella"]).any()
    )
    assert (
        got.codes["hoffa_fat_pad"] == "abstain_no_patella"
    )  # unknown here, not absent


def test_a_twin_that_cannot_be_read_says_why_and_keeps_the_planes_own_naming():
    objects = np.zeros((12, 12), np.int8)
    objects[2:4, 2:4] = A.OBJECT_CODES["patella"]
    plane = run.PatellaPlane(
        1, False, "identified", {}, "", "", None, None, objects, None, None, None
    )
    own = view()
    none = run.twin_reading(cast(Any, own), None, plane)
    assert none.code == "none_of_the_other_sequence" and none.pad_code == none.code
    assert set(none.tendon_codes.values()) == {"none_of_the_other_sequence"}
    assert (none.fs_objects == objects).all() and none.slice is None
    blind = SimpleNamespace(series=SimpleNamespace(volume=None))
    assert (
        run.twin_reading(cast(Any, own), cast(Any, blind), plane).code
        == "no_stacked_volume"
    )


def test_observations_are_added_after_the_earlier_ones_and_recounted():
    own = view()
    old = run.observe(
        "femur",
        "native",
        "resolved",
        cast(Any, own),
        (0,),
        "identified",
        3,
        0.0,
        "a1_objects",
        "n",
        "a.npz",
    )
    own.record["observations"] = run.observation_rows([old])
    own.record["observations_unresolved"] = []
    new = run.observe(
        "patella",
        "projected",
        "target",
        cast(Any, own),
        (1,),
        "on_the_slice",
        4,
        0.5,
        "x",
        "n",
        "a.npz",
    )
    run.keep_observations(
        cast(Any, own), [new], [run.Unresolved("patella", "native", "w", None, "why")]
    )
    rows = own.record["observations"]
    assert [r["object"] for r in rows] == ["femur", "patella"]
    assert own.record["observations_by_provenance"] == {
        "native": 1,
        "laid": 0,
        "projected": 1,
    }
    assert own.record["observations_unresolved"][0]["code"] == "why"
