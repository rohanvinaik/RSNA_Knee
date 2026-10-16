"""The joint's collapse: the corridor, the four quantities, pointing, compartments, failures."""

from types import SimpleNamespace
from typing import Any, cast

import numpy as np

from knee.collapse import joint as J
from knee.collapse.physical import PlaneFrame, physical_squint
from knee.collapse.profile import positive_runs, run_maxima
from knee.objects import assignments as A
from knee.telemetry import computing, recording
from scripts import run_interiors as run

PITCH = 1.5


def frame() -> PlaneFrame:
    # rows run along the leg (z), columns along y
    return PlaneFrame(
        np.zeros(3), np.array([[0.0, 0.0], [0.0, 1.5], [1.5, 0.0]]), (PITCH, PITCH)
    )


def test_corridor_is_between_the_bones_and_empty_when_one_bone_is_missing():
    femur = np.zeros((30, 30), bool)
    tibia = np.zeros((30, 30), bool)
    femur[16:] = True  # superior lies toward larger rows in this frame
    tibia[:10] = True
    f = frame()
    corridor, reach = J.joint_reach(femur, tibia, f.basis_lps, np.asarray(f.spacing_rc))
    assert corridor[10:16].all() and not corridor[:10].any() and not corridor[16:].any()
    assert reach.sum() > corridor.sum()
    none, _ = J.joint_reach(
        femur, np.zeros_like(tibia), f.basis_lps, np.asarray(f.spacing_rc)
    )
    assert not none.any()


def test_levels_without_a_usable_anchor_are_none_not_a_level():
    got = J.levels(5.0, float("nan"), 0.0)
    assert got[J.DARK] is not None
    assert got[J.LIGAMENT] is None and got[J.BRIGHT] is None and got[J.FLUID] is None
    assert J.levels(float("nan"), 100.0, 100.0)[J.DARK] is None


def test_block_support_keeps_unseen_blocks_apart_from_dark_and_light():
    median = np.array([[1.0, 200.0], [np.nan, 50.0]])
    held = np.ones((2, 2), bool)
    area, seen, unseen = J.block_support(
        median,
        held,
        (2.0, 2.0),
        {
            J.DARK: (-np.inf, 5.0),
            J.BRIGHT: (150.0, np.inf),
            J.LIGAMENT: (-np.inf, 50.0),
        },
    )
    assert area[J.DARK] == 4.0 and area[J.BRIGHT] == 4.0
    assert area[J.LIGAMENT] == 4.0  # strictly under 50: only the 1.0 block
    assert seen == 3 and unseen == 1


def test_a_sagittal_plane_is_sided_by_the_header_and_never_guessed():
    assert J.compartment("R", 5.0) == "medial"
    assert J.compartment("R", -5.0) == "lateral"
    assert J.compartment("L", 5.0) == "lateral"
    assert J.compartment("", 5.0) == "meniscus"
    assert J.compartment("R", 0.0) == "meniscus"
    assert J.compartment("R", float("nan")) == "meniscus"


def test_horns_are_the_pieces_nearest_each_end_along_the_plane_axis():
    dark = np.zeros((30, 60), bool)
    dark[10:16, 2:12] = True  # front piece
    dark[10:16, 46:58] = True  # back piece
    joint = np.zeros_like(dark)
    joint[12:14, 5:55] = True
    back = np.broadcast_to(np.arange(60.0), (30, 60))
    cand, ends = J.horn_pieces(
        dark, joint, np.zeros_like(dark), np.array([1.0, 1.0]), back
    )
    assert cand.any() and (ends == 1).any() and (ends == 2).any()
    assert ends[12, 5] == 1 and ends[12, 50] == 2
    none, e = J.horn_pieces(
        dark, np.zeros_like(dark), np.zeros_like(dark), np.array([1.0, 1.0]), back
    )
    assert not none.any() and not e.any()


# -- the profile through the real joint_profile --------------------------------------------------
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


def profile(monkeypatch, planes, level, names=(J.DARK, J.BRIGHT), unseen=None):
    f = frame()
    shape = planes[0].shape
    femur = np.zeros(shape, bool)
    tibia = np.zeros(shape, bool)
    femur[16:] = True
    tibia[:10] = True
    monkeypatch.setattr(run, "plane_frame", lambda s, z: f)
    monkeypatch.setattr(
        run,
        "seen_native",
        lambda s, z, stage="x": (
            np.asarray(planes[z], float),
            np.zeros(shape, bool) if unseen is None else unseen,
        ),
    )
    monkeypatch.setattr(
        run,
        "bone_footprint",
        lambda _s, _z, _fr, _sh, _places, key: femur if key == "f" else tibia,
    )
    monkeypatch.setattr(run, "digest", lambda a: "f" if len(a) == 1 else "t")
    with computing(), recording() as led:
        got = run.joint_profile(
            cast(Any, Plain(planes)),
            cast(Any, stack_for(planes)),
            np.zeros((1, 3)),
            np.zeros((2, 3)),
            level,
            names,
        )
    return got, led


def plane(dark=False, bright=False):
    p = np.full((30, 30), 100.0)
    if dark:
        p[11:15, :] = 1.0
    if bright:
        p[11:15, :] = 900.0
    return p


LEVEL = {
    J.DARK: (-np.inf, 5.0),
    J.BRIGHT: (150.0, np.inf),
    J.FLUID: (400.0, np.inf),
    J.LIGAMENT: None,
}


def test_each_quantity_is_its_own_profile_and_a_plateau_keeps_every_tie(monkeypatch):
    got, led = profile(
        monkeypatch,
        [plane(dark=True), plane(dark=True), plane(bright=True), plane()],
        LEVEL,
    )
    d = got.area_mm2[J.DARK]
    runs = positive_runs(d)
    assert runs == [(0, 2)] and run_maxima(d, runs)[0].tolist() == [0, 1]
    assert got.status[J.DARK][3] == A.FIBULA_POINTER_STATUS["none"] and d[3] == 0.0
    b = got.area_mm2[J.BRIGHT]
    assert b[2] > 0 and b[0] == 0.0  # not combined: the bright one is not the dark one
    assert "joint.cheap_readings" in {e.name for e in led.events()}


def test_unseen_places_are_unknown_and_an_unusable_level_excludes_nothing(monkeypatch):
    shape = (30, 30)
    hidden = np.ones(shape, bool)
    got, _ = profile(monkeypatch, [plane(dark=True)], LEVEL, unseen=hidden)
    assert got.status[J.DARK][0] == A.FIBULA_POINTER_STATUS["unreadable"]
    assert np.isnan(got.area_mm2[J.DARK][0])
    got, _ = profile(monkeypatch, [plane()], LEVEL, names=(J.DARK, J.LIGAMENT))
    assert got.status[J.LIGAMENT][0] == A.FIBULA_POINTER_STATUS["unreadable"]
    nonfinite = np.full(shape, np.nan)
    got, _ = profile(monkeypatch, [nonfinite], LEVEL)
    assert got.status[J.DARK][0] == A.FIBULA_POINTER_STATUS["unreadable"]


def test_a_slice_with_no_joint_is_not_read_never_empty(monkeypatch):
    got, _ = profile(monkeypatch, [plane()], LEVEL)
    monkeypatch.setattr(run, "bone_footprint", lambda *a: np.zeros((30, 30), bool))
    with computing(), recording():
        none = run.joint_profile(
            cast(Any, Plain([plane()])),
            cast(Any, stack_for([plane()])),
            np.zeros((1, 3)),
            np.zeros((2, 3)),
            LEVEL,
            (J.DARK,),
        )
    assert none.status[J.DARK][0] == A.FIBULA_POINTER_STATUS["not_read"]
    assert np.isnan(none.area_mm2[J.DARK][0]) and got.corridor_px[0] > 0


def test_a_plane_whose_geometry_cannot_be_read_is_a_code_not_a_crash(monkeypatch):
    monkeypatch.setattr(run, "plane_frame", lambda s, z: "geometry_unreadable")
    own = SimpleNamespace(
        series=SimpleNamespace(row=SimpleNamespace(series_uid="w")), record={}
    )
    got = run.joint_plane(
        cast(Any, own),
        1,
        np.zeros((1, 3)),
        np.zeros((1, 3)),
        ("a", "b"),
        (J.DARK,),
        None,
    )
    assert got.code == run.UNREADABLE_GEOMETRY and got.objects is None


def test_the_axial_and_unnamed_series_say_why_and_a_twin_failure_is_a_code():
    own = SimpleNamespace(
        series=SimpleNamespace(
            row=SimpleNamespace(series_uid="w", fat_suppression="1"), volume=[]
        ),
        record={"assignments": {"femur": None, "tibia": None, "codes": {}}},
        arrays={"a1_objects": np.zeros((4, 4), np.int8)},
        assignment=SimpleNamespace(in_plane=(True, True, False)),
    )
    leg = cast(
        Any, SimpleNamespace(femur_lps=np.zeros((1, 3)), tibia_lps=np.zeros((1, 3)))
    )
    assert (
        run.read_joint(cast(Any, own), None, leg)
        == "abstain_leg_runs_through_the_plane"
    )
    own.assignment = SimpleNamespace(in_plane=(True, True, True))
    assert (
        run.read_joint(cast(Any, own), None, leg)
        == "bones_not_named_on_the_middle_slice"
    )
    objects = np.zeros((4, 4), np.int8)
    objects[0, 0] = A.OBJECT_CODES["mcl"]
    pl = run.JointPlane(
        1,
        False,
        "read",
        {},
        "",
        "",
        None,
        None,
        objects,
        None,
        None,
        None,
        None,
        None,
        (),
    )
    assert run.joint_twin(cast(Any, own), None, pl).code == "none_of_the_other_sequence"


def joint_plane_with(codes, middle=False):
    return run.JointPlane(
        1,
        middle,
        "read",
        codes,
        "",
        "",
        None,
        None,
        None,
        None,
        None,
        None,
        None,
        None,
        (),
    )


def test_what_a_rule_says_of_a_plane_keeps_candidates_apart_from_names():
    named = joint_plane_with({"pcl": "identified"})
    cand = joint_plane_with({"horns": run.HORNS, "meniscus": "abstain_x"})
    none = joint_plane_with({"pcl": "abstain_x"})
    assert run.says_of(named, J.LIGAMENT, {}) == "confirmed"
    assert run.says_of(cand, J.DARK, {}) == "candidates"
    assert run.says_of(none, J.LIGAMENT, {}) == "rejected"
    assert run.says_of(joint_plane_with({}, True), J.FLUID, {}) == "not_read"
