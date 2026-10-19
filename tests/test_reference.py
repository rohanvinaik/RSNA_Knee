"""The study's anatomical reference and the patella search that reads relative to it: the strongest
supported body asked first and widened only to another supported slice, ties kept, nothing read that
the cheap profile did not point to; a reference's place along a series' normal from physical places
(a reversed stack, unequal spacing and the other knee give the same offset); an unknown anywhere
gives no window and the whole depth is read; a window that does not name the patella is broadened;
the planes read stop at the first run that names it."""

from types import SimpleNamespace
from typing import Any, cast

import numpy as np

from knee.collapse.physical import PlaneFrame
from knee.collapse.reference import (
    Reference,
    expected_slices,
    offset_sign,
    patient_axis,
    reference_position,
    strongest_first,
)
from knee.objects import assignments as A
from knee.telemetry import computing, recording
from scripts import run_interiors as run

NORMAL_X = np.array([1.0, 0.0, 0.0])


# -- the pure measurements --------------------------------------------------------------------------
def test_a_reversed_normal_gives_the_same_offset_toward_the_left():
    forward = offset_sign(NORMAL_X, "Coronal", "")
    backward = offset_sign(-NORMAL_X, "Coronal", "")
    assert forward is not None and backward is not None
    # a place 6 mm toward the patient's left of the reference, whichever way the stack runs
    assert forward[0] * (16.0 - 10.0) == backward[0] * (-16.0 - -10.0) == 6.0
    assert forward[1] == backward[1] == "left"


def test_the_medial_sign_follows_the_knee_and_unknowns_stay_none():
    right = offset_sign(NORMAL_X, "Sagittal", "R")
    left = offset_sign(NORMAL_X, "Sagittal", "L")
    assert right == (1.0, "medial") and left == (-1.0, "medial")
    assert offset_sign(NORMAL_X, "Sagittal", "") == (1.0, "left")
    assert offset_sign(np.array([0.0, 0.0, 1.0]), "Axial", "R") is None
    assert offset_sign(np.zeros(3), "Sagittal", "R") is None
    assert patient_axis(np.array([np.nan, 0, 1])) is None


def test_the_strongest_candidate_is_asked_first_and_a_tie_is_one_group():
    area = np.array([0.0, 10.0, 40.0, np.nan, 40.0, 25.0, 0.0])
    assert strongest_first(area) == [(0, (2, 4)), (1, (5,)), (1, (1,))]
    assert strongest_first(np.array([np.nan, 0.0])) == []


def test_the_planes_the_profile_points_to_are_asked_before_any_other_supported_slice():
    # runs (1, 3) and (4, 5): their maxima are slices 2 and 4; slice 1 is supported but not a maximum
    area = np.array([0.0, 90.0, 100.0, 0.0, 60.0, 0.0])
    assert strongest_first(area) == [(0, (2,)), (0, (4,)), (1, (1,))]


def test_a_plane_across_the_axis_supplies_depth_and_a_spread_support_a_landmark():
    flat = np.array([[10.0, y, z] for y in range(5) for z in range(5)])
    got = reference_position(flat, NORMAL_X, thickness_mm=3.0)
    assert got is not None and got[0] == 10.0 and got[3] == "depth"
    spread = np.array([[x, y, 0.0] for x in range(-10, 30, 4) for y in range(3)])
    got = reference_position(spread, NORMAL_X, thickness_mm=3.0)
    assert got is not None and got[3] == "in_plane" and got[0] == spread[:, 0].mean()
    assert reference_position(np.empty((0, 3)), NORMAL_X, 3.0) is None
    assert reference_position(np.full((2, 3), np.nan), NORMAL_X, 3.0) is None
    assert reference_position(flat, np.zeros(3), 3.0) is None


def test_the_expected_slices_follow_physical_places_not_indices():
    places = np.array(
        [0.0, 3.0, 6.0, 9.0, 12.0, 15.0, 30.0]
    )  # unequal spacing at the end
    inside = expected_slices(places, 9.0, 1.0, (-4.0, 4.0), always=0)
    assert inside is not None and inside.tolist() == [
        True,
        False,
        True,
        True,
        True,
        False,
        False,
    ]
    # the same stack stored the other way round, the normal reversed: the same physical slices
    flipped = expected_slices(-places[::-1], -9.0, -1.0, (-4.0, 4.0), always=6)
    assert flipped is not None and flipped.tolist()[::-1] == inside.tolist()[:-1] + [
        False
    ]
    assert expected_slices(np.array([0.0, np.nan]), 0.0, 1.0, (-1.0, 1.0), 0) is None
    assert expected_slices(places, float("nan"), 1.0, (-1.0, 1.0), 0) is None


# -- the driver: a stack of slices along x, 3 mm apart ---------------------------------------------
DEPTH = 12


def sagittal_frame() -> PlaneFrame:
    # rows run toward the feet, columns toward the back: the normal is x
    basis = np.array([[0.0, 0.0], [0.0, 1.5], [-1.5, 0.0]])
    return PlaneFrame(np.zeros(3), basis, (1.5, 1.5))


def reference_at(x: float, kind_spread: float = 0.0) -> Reference:
    support = np.array([[x + kind_spread * k, 0.0, 0.0] for k in (-1, 0, 1)])
    return Reference(
        "ref",
        ("Sagittal", "0", "0"),
        "tibia",
        (4,),
        100.0,
        support,
        np.array([x, 0.0, 0.0]),
        NORMAL_X,
        3.0,
        "R",
        "test",
        (),
    )


def view(knee="R", positions=None):
    shape = (12, 12)
    objects = np.zeros(shape, np.int8)
    objects[0:4] = A.OBJECT_CODES["femur"]
    places = [3.0 * k for k in range(DEPTH)] if positions is None else positions
    return SimpleNamespace(
        series=SimpleNamespace(
            row=SimpleNamespace(
                series_uid="p", fat_suppression="1", fluid_sensitive="1"
            ),
            volume=[np.full(shape, 100.0)] * DEPTH,
            geometry=SimpleNamespace(
                position=[np.array([p, 0.0, 0.0]) for p in places]
            ),
            slice_thickness_mm=tuple([3.0] * DEPTH),
        ),
        record={
            "series_uid": "p",
            "slice_index": 0,
            "background_split": 1.0,
            "assignments": {"femur": 1, "codes": {}, "knee": knee},
            "view": ["Sagittal", "1", "1"],
        },
        arrays={"a1_objects": objects, "acquired_plane": np.full(shape, 100.0)},
        assignment=SimpleNamespace(in_plane=(False, True, True)),
        stack=SimpleNamespace(code="present"),
        frame=sagittal_frame(),
    )


def test_a_window_is_the_cohort_range_around_the_references_place(monkeypatch):
    monkeypatch.setitem(run.PATELLA_FROM_REFERENCE_MM, ("depth", "left"), (-4.0, 4.0))
    own = view()
    window, said = run.patella_neighbourhood(cast(Any, own), reference_at(10.0))
    assert window is not None and said["code"] == "window"
    assert np.flatnonzero(window).tolist() == [0, 2, 3, 4]  # 0 is the middle slice
    assert said["convention"] == "left" and said["slices_in"] == 4
    # the same slices stored from the other end, and the normal pointing the other way
    back = view(positions=[33.0 - 3.0 * k for k in range(DEPTH)])
    back.frame = PlaneFrame(
        np.zeros(3), np.array([[0.0, 0.0], [0.0, 1.5], [1.5, 0.0]]), (1.5, 1.5)
    )
    assert float(back.frame.normal()[0]) < 0
    other, _ = run.patella_neighbourhood(cast(Any, back), reference_at(10.0))
    assert other is not None
    # the physical slices in range are the same ones (x = 6, 9, 12), plus the middle slice
    assert sorted(33.0 - 3.0 * k for k in np.flatnonzero(other) if k) == [
        6.0,
        9.0,
        12.0,
    ]


def test_an_unknown_gives_no_window_and_says_which(monkeypatch):
    monkeypatch.setitem(run.PATELLA_FROM_REFERENCE_MM, ("depth", "left"), (-4.0, 4.0))
    own = cast(Any, view())
    assert run.patella_neighbourhood(own, "no_confirmed_key_plane") == (
        None,
        {"code": "no_reference_no_confirmed_key_plane"},
    )
    window, said = run.patella_neighbourhood(own, reference_at(10.0, kind_spread=20.0))
    assert window is None and said["code"].startswith(
        "no_cohort_range"
    )  # an in-plane landmark
    nan_places = [3.0 * k for k in range(DEPTH)]
    nan_places[5] = float("nan")
    window, said = run.patella_neighbourhood(
        cast(Any, view(positions=nan_places)), reference_at(10.0)
    )
    assert window is None and "unsound" in said["code"]
    axial = view()
    axial.frame = PlaneFrame(
        np.zeros(3), np.array([[1.5, 0.0], [0.0, 1.5], [0.0, 0.0]]), (1.5, 1.5)
    )
    window, said = run.patella_neighbourhood(cast(Any, axial), reference_at(10.0))
    assert window is None and said["code"].startswith("no_cohort_range")


def patella_search(monkeypatch, area, named, reference, knee="R"):
    """read_patella with the cheap profile given (`area`, NaN where a slice is not visited) and
    the planes in `named` naming the patella; returns the read, the planes asked and the ledger."""
    monkeypatch.setitem(run.PATELLA_FROM_REFERENCE_MM, ("depth", "left"), (-4.0, 4.0))
    shape = (12, 12)
    asked: list[int] = []
    own = view(knee=knee)
    monkeypatch.setattr(run, "plane_frame", lambda s, z: own.frame)
    monkeypatch.setattr(
        run, "measures_of", lambda *a: SimpleNamespace(light=lambda mask: 100.0)
    )

    def fake_profile(*args):
        visit = args[8]
        seen = np.ones(DEPTH, bool) if visit is None else np.asarray(visit)
        values = np.where(seen, np.asarray(area, float), np.nan)
        status = np.where(
            seen, A.FIBULA_POINTER_STATUS["body"], A.FIBULA_POINTER_STATUS["not_read"]
        ).astype(np.int8)
        return run.BoneProfile(
            status,
            values,
            np.ones(DEPTH, np.int32),
            np.zeros(DEPTH, bool),
            np.zeros((DEPTH, 1, 1), bool),
            np.zeros((DEPTH, 1, 1), bool),
            np.zeros((DEPTH, 1, 1), bool),
            np.full((DEPTH, 4), -1, np.int32),
            np.full((DEPTH, 2), np.nan),
            np.full((DEPTH, 2), -1, np.int32),
            (),
            100.0,
        )

    def fake_plane(_own, z, *rest, **kwargs):
        assert set(kwargs) == {"profile_window", "reference"}
        assert isinstance(kwargs["reference"], run.NativeMiddleReference)
        assert kwargs["reference"].source_series_uid == own.series.row.series_uid
        asked.append(z)
        objects = np.zeros(shape, np.int8)
        code = "abstain_no_peak_in_front_of_the_femur"
        if z in named:
            objects[2:5, 2:5] = A.OBJECT_CODES["patella"]
            code = "identified"
        return run.PatellaPlane(
            z,
            False,
            code,
            {},
            "identified",
            "identified",
            np.zeros(shape, np.int32),
            np.ones(shape, bool),
            objects,
            None,
            100.0,
            None,
        )

    monkeypatch.setattr(run, "bone_profile", lambda *a: fake_profile(*a))
    monkeypatch.setattr(run, "patella_plane", fake_plane)
    monkeypatch.setattr(run, "twin_reading", lambda *a: None)
    pts = np.zeros((4, 3))
    pts[:, 1] = -40.0
    with computing(), recording() as led:
        got = run.read_patella(cast(Any, own), None, pts, pts, reference)
    assert isinstance(got, run.PatellaRead)
    return got, asked, led


RUNS = [
    0,
    0,
    50,
    100,
    60,
    0,
    0,
    0,
    100,
    200,
    100,
    0,
]  # a weak run in range, a strong one beyond


def test_the_expected_neighbourhood_is_read_first_and_the_stronger_run_beyond_stays_a_pointer(
    monkeypatch,
):
    got, asked, led = patella_search(monkeypatch, RUNS, {3, 9}, reference_at(10.0))
    search = got.record["search"]
    assert asked == [3] and search["code"] == "window"
    assert (
        search["stopped"].startswith("a_run_named")
        and not search["broadened_to_the_whole_depth"]
    )
    assert search["slices_unvisited"] == [1, 5, 6, 7, 8, 9, 10, 11]
    assert got.outcome == "identified"
    # the run beyond the window was never visited: unknown, never empty
    assert np.isnan(got.arrays["a3_patella_profile_area_mm2"][9])
    assert (
        "slices_outside_the_expected_neighbourhood_were_not_visited_unknown_not_empty"
        in got.record["ambiguities"]
    )
    assert {e.name for e in led.events()} >= {
        "patella.window_slices_in",
        "patella.window_slices_unvisited",
    }


def test_a_run_cut_by_the_window_is_walked_to_its_own_peak_not_asked_at_the_edge(
    monkeypatch,
):
    rising = [0, 0, 10, 20, 30, 40, 50, 60, 50, 0, 0, 0]  # the window ends at slice 4
    got, asked, led = patella_search(monkeypatch, rising, {4, 7}, reference_at(10.0))
    search = got.record["search"]
    assert asked == [7] and got.outcome == "identified"
    # read to the peak and one beyond it to see that it is one; nothing further
    assert search["slices_unvisited"] == [1, 9, 10, 11]
    walked = sum(
        e.counts["planes"] for e in led.events() if e.name == "patella.walked_slices"
    )
    assert walked == 4 and not search["broadened_to_the_whole_depth"]


def test_a_window_that_does_not_name_the_patella_is_broadened_to_the_rest(monkeypatch):
    got, asked, _ = patella_search(monkeypatch, RUNS, {9}, reference_at(10.0))
    search = got.record["search"]
    assert asked == [3, 9] and search["broadened_to_the_whole_depth"]
    assert search["slices_unvisited"] == [] and got.outcome == "identified"
    assert got.arrays["a3_patella_search_visited"].all()
    assert not got.arrays["a3_patella_search_window"].all()


def test_nothing_named_anywhere_reads_every_pointed_plane_and_is_unresolved(
    monkeypatch,
):
    got, asked, _ = patella_search(monkeypatch, RUNS, set(), reference_at(10.0))
    assert sorted(asked) == [3, 9] and got.outcome == "unresolved"


def test_no_reference_reads_the_whole_depth_strongest_run_first_and_stops_when_named(
    monkeypatch,
):
    got, asked, _ = patella_search(monkeypatch, RUNS, {9, 3}, "no_confirmed_key_plane")
    assert asked == [9]  # the strongest run names it: the weaker run stays a pointer
    assert got.record["search"]["code"].startswith("no_reference")
    assert got.record["search"]["passes"] == 1
    assert got.arrays["a3_patella_pointer_run_native_rule"].tolist() == [
        run.RUN_CONFIRMATION["not_read_natively"],
        run.RUN_CONFIRMATION["confirmed_by_the_native_rule"],
    ]
    assert got.record["search"]["planes_the_profile_pointed_to"] == [3, 9]


def test_a_tied_strongest_run_asks_every_tied_slice(monkeypatch):
    area = [0, 0, 100, 100, 0, 0, 0, 0, 0, 0, 0, 0]
    _, asked, _ = patella_search(monkeypatch, area, set(), "none")
    assert sorted(asked) == [2, 3]


# -- the reference selection --------------------------------------------------------------------------
# strongest first, in order of area


def test_a_window_pass_merged_with_the_rest_is_the_whole_depth_profile():
    rng = np.random.default_rng(1)
    depth = 6
    base = rng.integers(1, 9, size=1000)

    def profile(visited):
        def field(*shape, dtype=float):
            n = int(np.prod(shape))
            values = base[:n].reshape(shape).astype(dtype)
            return np.where(
                visited.reshape(-1, *([1] * (len(shape) - 1))),
                values,
                np.zeros(shape, dtype),
            )

        return run.BoneProfile(
            field(depth, dtype=np.int8),
            field(depth),
            field(depth, dtype=np.int32),
            field(depth, dtype=bool),
            field(depth, 2, 2, dtype=bool),
            field(depth, 2, 2, dtype=bool),
            field(depth, 2, 2, dtype=bool),
            field(depth, 4, dtype=np.int32),
            field(depth, 2),
            field(depth, 2, dtype=np.int32),
            (),
            1.0,
        )

    inside = np.array([False, True, True, True, False, False])
    first, second = profile(inside), profile(~inside)
    merged = run.merge_profiles(first, second, ~inside)
    assert np.array_equal(merged.area_mm2[inside], first.area_mm2[inside])
    assert np.array_equal(merged.area_mm2[~inside], second.area_mm2[~inside])
    assert merged.corridor.shape == first.corridor.shape


# -- one value, many consumers --------------------------------------------------------------------------
def test_the_references_profile_and_plane_are_made_once_for_the_bones_own_reading(
    monkeypatch,
):
    shape = (12, 12)
    own = view()
    own.series.row.fat_suppression = "0"
    f = sagittal_frame()
    made = {"profile": 0, "lens": 0}

    def profile(*args):
        made["profile"] += 1
        return SimpleNamespace(area_mm2=np.zeros(DEPTH), fine=())

    def lens(*args, **kwargs):
        made["lens"] += 1
        labels = np.zeros(shape, np.int32)
        return run.InteriorRegions(
            "present",
            np.zeros(shape, bool),
            np.ones(shape, bool),
            np.zeros(shape, dtype=np.float64),
            np.zeros(shape, dtype=np.int32),
            labels,
        )

    monkeypatch.setattr(run, "bone_profile", profile)
    monkeypatch.setattr(run, "interior_regions", lens)
    monkeypatch.setattr(run, "plane_frame", lambda s, z: f)
    monkeypatch.setattr(run, "bone_footprint", lambda *a: np.zeros(shape, bool))
    places = np.zeros((3, 3))
    with computing(), recording():
        first = run.bone_profile_of(cast(Any, own), "femur", places, places, 100.0)
        again = run.bone_profile_of(cast(Any, own), "femur", places, places, 100.0)
        one = run.bone_plane_read(
            cast(Any, own), "femur", 3, places, places, first, "reference"
        )
        two = run.bone_plane_read(
            cast(Any, own), "femur", 3, places, places, first, "bones"
        )
    assert again is first and two is one
    assert made == {"profile": 1, "lens": 1}
