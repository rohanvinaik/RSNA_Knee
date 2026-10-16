"""The recess family: the compartments' relations, the fluid pointer, the planes it asks, failures."""

from types import SimpleNamespace
from typing import Any, cast

import numpy as np

from knee.collapse import recess as R
from knee.collapse.joint import FLUID
from knee.collapse.physical import PlaneFrame, physical_squint
from knee.collapse.profile import positive_runs, run_maxima
from knee.objects import assignments as A
from knee.telemetry import computing, recording
from scripts import run_interiors as run

PITCH = 1.5
NONE = A.FIBULA_POINTER_STATUS["none"]
UNREADABLE = A.FIBULA_POINTER_STATUS["unreadable"]


def grid(shape=(4, 5)):
    """Places with x along columns, y along rows, z = 10."""
    rows, cols = np.indices(shape)
    return np.stack([cols, rows, np.full(shape, 10.0)], axis=-1).astype(float)


def test_anterior_pocket_is_between_patella_and_femur_above_the_patella_foot():
    p = grid()
    got = R.anterior_pocket(p, 0.5, 2.5, 10.0)
    assert got[1:3].all() and not got[0].any() and not got[3].any()
    assert not R.anterior_pocket(p, 0.5, 2.5, 11.0).any()  # below the patella's foot
    assert not R.anterior_pocket(p, float("nan"), 2.5, 10.0).any()
    p[1, 1, 2] = np.nan
    assert not R.anterior_pocket(p, 0.5, 2.5, 10.0)[1, 1]  # nonfinite is no place
    # reversed order of the places changes nothing: it is a relation in millimetres
    assert (
        R.anterior_pocket(p[::-1, ::-1], 0.5, 2.5, 10.0)
        == R.anterior_pocket(p, 0.5, 2.5, 10.0)[::-1, ::-1]
    ).all()


def test_gutters_are_outboard_of_both_menisci_inside_the_femur_and_above_the_joint():
    marks = R.gutter_landmarks(
        np.array([3.0, 3.0]), np.array([1.0, 1.0]), np.array([5.0]), np.array([4.0])
    )
    assert marks == ((1.0, 3.0), 4.0)
    assert (
        R.gutter_landmarks(
            np.array([]), np.array([1.0]), np.array([1.0]), np.array([1.0])
        )
        is None
    )
    p = grid((3, 7))
    got = R.side_gutters(p, (2.0, 4.0), 5.0, (0.0, 5.0))
    assert got[:, [0, 1, 5]].all() and not got[:, 6].any()
    assert not got[:, 2:5].any()  # between the menisci: the joint, not a gutter
    assert not R.side_gutters(
        p, (2.0, 4.0), 11.0, (0.0, 5.0)
    ).any()  # below the joint line
    assert not R.side_gutters(p, (2.0, np.nan), 5.0, (0.0, 5.0)).any()


def test_the_retinacular_interval_runs_front_to_femur_and_is_empty_when_reversed():
    p = grid((6, 6))
    got = R.patellofemoral_interval(p, 1.0, 4.0, (1.0, 4.0))
    assert got[1:5, 1:5].all() and not got[0].any() and not got[5].any()
    assert not R.patellofemoral_interval(p, 4.0, 1.0, (1.0, 4.0)).any()
    assert not R.patellofemoral_interval(p, 1.0, 4.0, (np.nan, 4.0)).any()


# -- the pointer through the real joint_profile, with a relation for its corridor -----------------
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


def frame() -> PlaneFrame:
    return PlaneFrame(
        np.zeros(3), np.array([[0.0, 0.0], [0.0, 1.5], [1.5, 0.0]]), (PITCH, PITCH)
    )


def pointer(monkeypatch, planes, reach_of, level=(300.0, np.inf), unseen=None):
    f = frame()
    shape = planes[0].shape
    monkeypatch.setattr(run, "plane_frame", lambda s, z: f)
    monkeypatch.setattr(
        run,
        "seen_native",
        lambda s, z, stage="x": (
            np.asarray(planes[z], float),
            np.zeros(shape, bool) if unseen is None else unseen,
        ),
    )
    with computing(), recording() as led:
        got = run.joint_profile(
            cast(Any, Plain(planes)),
            cast(Any, stack_for(planes)),
            np.empty((0, 3)),
            np.empty((0, 3)),
            {FLUID: level},
            (FLUID,),
            lambda z, _frame, sh: reach_of(z, sh),
            "recess",
        )
    return got, led


def plane(white=False):
    p = np.full((30, 30), 100.0)
    if white:
        p[11:15, 11:15] = 900.0
    return p


def box(z, shape):
    reach = np.zeros(shape, bool)
    reach[8:18, 8:18] = True
    return reach


def test_a_plateau_keeps_every_tie_and_a_slice_without_a_corridor_is_not_read(
    monkeypatch,
):
    skip = {3}

    def reach(z, shape):
        return np.zeros(shape, bool) if z in skip else box(z, shape)

    got, led = pointer(
        monkeypatch, [plane(True), plane(True), plane(), plane(True)], reach
    )
    area = got.area_mm2[FLUID]
    runs = positive_runs(area)
    assert runs == [(0, 2)] and run_maxima(area, runs)[0].tolist() == [0, 1]
    assert got.status[FLUID][2] == NONE and area[2] == 0.0  # read, measured absent
    assert got.status[FLUID][3] == A.FIBULA_POINTER_STATUS["not_read"]
    assert np.isnan(area[3])  # no corridor: nothing said, never zero
    names = {e.name for e in led.events()}
    assert "recess.cheap_readings" in names and "joint.cheap_readings" not in names


def test_unseen_nonfinite_and_unusable_level_are_unknown_never_measured_absence(
    monkeypatch,
):
    hidden = np.ones((30, 30), bool)
    got, _ = pointer(monkeypatch, [plane(True)], box, unseen=hidden)
    assert got.status[FLUID][0] == UNREADABLE and np.isnan(got.area_mm2[FLUID][0])
    got, _ = pointer(monkeypatch, [np.full((30, 30), np.nan)], box)
    assert got.status[FLUID][0] == UNREADABLE
    got, _ = pointer(monkeypatch, [plane()], box, level=None)  # type: ignore[arg-type]
    assert got.status[FLUID][0] == UNREADABLE


def test_partial_coarse_coverage_is_unknown_not_absent(monkeypatch):
    p = plane()
    p[:, :14] = np.nan  # a strip of tiles never seen, in reach of the corridor
    got, _ = pointer(monkeypatch, [p], box)
    assert got.status[FLUID][0] == UNREADABLE


# -- the corridors ------------------------------------------------------------------------------
def own_with(arrays, record):
    return SimpleNamespace(
        series=SimpleNamespace(row=SimpleNamespace(series_uid="w")),
        record=record,
        arrays=arrays,
    )


def test_the_anterior_corridor_reads_only_where_the_patella_is_and_says_why():
    marks = A.FIBULA_POINTER_STATUS
    status = np.array(
        [
            marks["body"],
            marks["none"],
            marks["unreadable"],
            marks["not_read"],
            marks["cut"],
        ]
    )
    objects = np.zeros((6, 6), np.int8)
    objects[2:4, 2:4] = A.OBJECT_CODES["patella"]
    own = own_with(
        {"a3_patella_profile_status": status, "a1_objects": objects},
        {
            "patella": {"pointed_planes": []},
            "assignments": {"codes": {"patella": "identified"}},
        },
    )
    own.frame = frame()
    leg = SimpleNamespace(femur_lps=np.array([[0.0, 5.0, 0.0], [0.0, 9.0, 0.0]]))
    why = np.zeros(5, np.int8)
    got = run.recess_corridor(cast(Any, own), "anterior", cast(Any, leg), None, why)
    assert not isinstance(got, str)
    reach, landmarks = got
    f = frame()
    assert reach(0, f, (6, 6)).any() and reach(4, f, (6, 6)).any()  # body, cut: asked
    for z, code in (
        (1, "patella_measured_absent_there"),
        (2, "patella_support_unknown_there"),
        (3, "patella_corridor_not_read_there"),
    ):
        assert not reach(z, f, (6, 6)).any()
        assert run.RECESS_REASONS[why[z]] == code
    assert landmarks["patella_sections"] == 1
    gone = own_with({}, {})
    assert (
        run.recess_corridor(cast(Any, gone), "anterior", cast(Any, leg), None, why)
        == "abstain_patella_not_profiled"
    )


def test_the_side_corridor_needs_both_menisci_named_by_an_earlier_family():
    own = own_with(
        {"a1_objects": np.zeros((4, 4), np.int8)},
        {"slice_index": 0, "joint": {"pointed_planes": []}},
    )
    leg = cast(Any, SimpleNamespace())
    assert (
        run.recess_corridor(cast(Any, own), "side", leg, None, np.zeros(3, np.int8))
        == "abstain_joint_not_read"
    )
    own.arrays["a3_joint_plane_objects"] = np.zeros((0, 4, 4), np.int8)
    assert (
        run.recess_corridor(cast(Any, own), "side", leg, None, np.zeros(3, np.int8))
        == "abstain_no_plane_names_both_menisci"
    )


# -- the planes ---------------------------------------------------------------------------------
def test_a_plane_whose_geometry_cannot_be_read_is_a_code_and_keeps_the_arrays(
    monkeypatch,
):
    monkeypatch.setattr(run, "plane_frame", lambda s, z: "geometry_unreadable")
    own = own_with({}, {})
    leg = SimpleNamespace(femur_lps=np.zeros((1, 3)), tibia_lps=np.zeros((1, 3)))
    got = run.recess_anterior_plane(
        cast(Any, own), 3, cast(Any, leg), ("a", "b"), {}, ("fluid",)
    )
    assert got.code == run.UNREADABLE_GEOMETRY and not got.masks
    side = run.recess_side_plane(
        cast(Any, own), 3, np.zeros((2, 2), np.int8), 0, ("fluid",)
    )
    assert side.code == run.UNREADABLE_GEOMETRY


def test_a_plane_the_patella_family_read_is_reused_and_never_read_again(monkeypatch):
    shape = (12, 12)
    objects = np.zeros(shape, np.int8)
    objects[0:3, 0:3] = A.OBJECT_CODES["femur"]
    objects[9:12, 9:12] = A.OBJECT_CODES["tibia"]
    objects[4:6, 0:3] = A.OBJECT_CODES["patella"]
    plane_values = np.full(shape, 10.0)
    plane_values[6:8, 4:6] = 900.0
    f = frame()
    monkeypatch.setattr(run, "plane_frame", lambda s, z: f)
    monkeypatch.setattr(
        run,
        "patella_plane",
        lambda *a, **k: (_ for _ in ()).throw(AssertionError("read again")),
    )
    own = SimpleNamespace(
        series=SimpleNamespace(
            row=SimpleNamespace(series_uid="r"), volume=[plane_values, plane_values]
        ),
        record={},
        arrays={"a3_patella_plane_objects": np.stack([objects])},
    )
    leg = SimpleNamespace(femur_lps=np.zeros((1, 3)), tibia_lps=np.zeros((1, 3)))
    with computing(), recording():
        got = run.recess_anterior_plane(
            cast(Any, own), 1, cast(Any, leg), ("a", "b"), {1: 0}, ("fluid",)
        )
    assert got.source == run.RECESS_SOURCES[0] and got.source_row == 0
    assert got.objects is None and got.labels is None  # the earlier family's are kept
    assert set(got.codes) == {"anterior_synovial_recess", "synovium", "joint_fluid"}
    assert got.masks["white"].any()


def test_the_twin_failures_are_codes_never_absence():
    own = SimpleNamespace(series=SimpleNamespace(row=SimpleNamespace(series_uid="w")))
    pl = run.recess_blank(1, "anterior", "read", ("fluid",))
    assert (
        run.recess_twin(cast(Any, own), None, pl, ("recess",)).code
        == "none_of_the_other_sequence"
    )
    twin = SimpleNamespace(series=SimpleNamespace(volume=None, geometry=None))
    assert (
        run.recess_twin(cast(Any, own), cast(Any, twin), pl, ("recess",)).code
        == "no_stacked_volume"
    )


def test_the_series_that_cannot_be_read_say_why():
    series = SimpleNamespace(
        row=SimpleNamespace(series_uid="w", fat_suppression="0", fluid_sensitive="0"),
        volume=[],
    )
    own = SimpleNamespace(
        series=series,
        record={},
        arrays={},
        assignment=SimpleNamespace(in_plane=(False, True, True)),
    )
    leg = cast(Any, SimpleNamespace())
    assert (
        run.read_recess(cast(Any, own), None, leg, None, {})
        == "abstain_fluid_not_bright_on_this_sequence"
    )
    series.row.fat_suppression = series.row.fluid_sensitive = "1"
    own.assignment = SimpleNamespace(in_plane=(False, False, True))
    assert (
        run.read_recess(cast(Any, own), None, leg, None, {})
        == "abstain_plane_not_read_by_a_relation"
    )


def test_what_a_rule_says_of_a_plane_and_the_feed_is_read_per_axial_series():
    named = run.recess_blank(
        1, "side", "read", (), False, {"joint_capsule": "identified"}
    )
    assert run.recess_says(named, {}) == "confirmed"
    none = run.recess_blank(
        1, "side", "read", (), False, {"joint_capsule": "abstain_x"}
    )
    assert run.recess_says(none, {}) == "rejected"
    boot = run.recess_blank(1, "side", "bootstrap", (), True)
    assert run.recess_says(boot, {}) == "not_read"
    assert run.recess_says(boot, {"joint_capsule": "identified"}) == "confirmed"
    m = SimpleNamespace(
        record={
            "patella": {
                "retinacula_feed": [
                    {"axial": [{"series_uid": "ax", "slice_from_every_section": 7}]}
                ]
            }
        }
    )
    other = SimpleNamespace(record={})
    assert run.recess_feed(cast(Any, [other, m])) == {"ax": 7}
    assert run.recess_feed(cast(Any, [other])) == {}


def test_the_arrays_keep_every_plane_even_one_that_failed():
    shape = (6, 6)
    ok = run.RecessPlane(
        4,
        False,
        "side",
        "read",
        {},
        run.RECESS_SOURCES[1],
        2,
        {"capsule": np.ones(shape, bool)},
        {"x": np.array([1.0, 2.0])},
        None,
        None,
        None,
        ("fluid",),
    )
    bad = run.recess_blank(7, "side", run.UNREADABLE_GEOMETRY, ("fluid",))
    out = run.stacked([ok.masks, bad.masks], "capsule", shape, bool)
    assert out.shape == (2, *shape) and out[0].all() and not out[1].any()
    vals = run.stacked([ok.values, bad.values], "x", (2,), np.float64)
    assert vals[0].tolist() == [1.0, 2.0] and np.isnan(vals[1]).all()
