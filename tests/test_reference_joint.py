"""The joint family searched relative to the study's reference: physical directions (a reversed
stack and unequal spacing give the same offset; the front-to-back axis is explicit and the head axis
stays unknown), a range wired only where the cohort supports one (none is: every search reads the
established depth, with its reason), selected visits that leave the rest NOT_READ and never empty,
a merge that reads no slice twice, runs walked to their peaks, questions that differ by view and by
side (a plane naming one meniscus leaves the other's question open), ties never broken, gated
quantities asked nothing, the shared reading of a plane pointed to by two quantities, and the rows
the recess family reads staying aligned with the planes read."""

from types import SimpleNamespace
from typing import Any, cast

import numpy as np

from knee.collapse.joint import BRIGHT, DARK, FLUID, LIGAMENT
from knee.collapse.physical import PlaneFrame
from knee.collapse.reference import (
    JOINT_FROM_REFERENCE_MM,
    Reference,
    offset_direction,
    offset_sign,
)
from knee.objects import assignments as A
from knee.telemetry import computing, recording
from scripts import run_interiors as run

DEPTH = 12
SHAPE = (12, 12)
Y = np.array([0.0, 1.0, 0.0])
X = np.array([1.0, 0.0, 0.0])


# -- the physical convention --------------------------------------------------------------------
def test_the_front_to_back_axis_is_explicit_and_reversed_stacks_agree():
    forward = offset_direction(Y, "Coronal", "")
    backward = offset_direction(-Y, "Coronal", "")
    assert forward is not None and backward is not None
    assert forward[1] == backward[1] == "posterior"
    # a place 6 mm toward the back of the reference, whichever way the stack runs
    assert forward[0] * (16.0 - 10.0) == backward[0] * (-16.0 - -10.0) == 6.0
    assert (
        offset_direction(np.array([0.0, 0.2, 1.0]), "Axial", "R") is None
    )  # head axis
    assert offset_direction(np.zeros(3), "Coronal", "R") is None


def test_the_left_right_axis_keeps_exactly_the_old_convention():
    for knee in ("R", "L", ""):
        for normal in (X, -X):
            assert offset_direction(normal, "Sagittal", knee) == offset_sign(
                normal, "Sagittal", knee
            )
    assert (
        offset_sign(Y, "Coronal", "") is None
    )  # the old function never learned the back axis


def test_no_cohort_range_is_wired_for_the_joint_because_none_showed_lift():
    assert JOINT_FROM_REFERENCE_MM == {}


# -- the questions, by view and by side -----------------------------------------------------------
def test_a_coronal_series_asks_each_side_and_the_cartilage_but_nothing_of_the_cruciates():
    asks = run.joint_questions(True, True, ("medial_meniscus", "lateral_meniscus"))
    assert asks == {
        "body:medial_meniscus": DARK,
        "body:lateral_meniscus": DARK,
        "mcl": DARK,
        "cartilage:femoral_cartilage": BRIGHT,
        "cartilage:tibial_cartilage": BRIGHT,
    }
    assert FLUID not in asks.values() and LIGAMENT not in asks.values()
    plain = run.joint_questions(True, False, ("meniscus",))
    assert plain == {
        "body:meniscus": DARK
    }  # no cartilage without fat suppression, no MCL unsided


def test_a_sagittal_series_asks_each_compartment_and_its_own_cruciate_question():
    fat = run.joint_questions(False, True, ("medial_meniscus", "lateral_meniscus"))
    assert fat == {
        "horns:medial_meniscus": DARK,
        "horns:lateral_meniscus": DARK,
        "cartilage_reading": BRIGHT,
        "acl": FLUID,
    }
    dry = run.joint_questions(False, False, ("medial_meniscus", "lateral_meniscus"))
    assert dry["pcl"] == LIGAMENT and "acl" not in dry


def plane_naming(z, names, codes=None, compartment=None, middle=False):
    objects = np.zeros(SHAPE, np.int8)
    for k, name in enumerate(names):
        objects[k : k + 1, 2:5] = A.OBJECT_CODES[name]
    return run.JointPlane(
        z,
        middle,
        "bootstrap" if middle else "read",
        codes or {},
        "identified",
        "identified",
        np.zeros(SHAPE, np.int32),
        np.ones(SHAPE, bool),
        objects,
        np.zeros(SHAPE, np.int8),
        np.zeros(SHAPE, np.int8),
        compartment,
        None,
        100.0,
        (),
    )


def test_a_plane_naming_one_meniscus_leaves_the_other_sides_question_open():
    medial = plane_naming(3, ["medial_meniscus"])
    got = run.joint_answers(medial, True)
    assert "body:medial_meniscus" in got and "body:lateral_meniscus" not in got
    both = run.joint_answers(
        plane_naming(4, ["medial_meniscus", "lateral_meniscus"]), True
    )
    assert {"body:medial_meniscus", "body:lateral_meniscus", "mcl"} <= both


def test_horn_candidates_answer_only_their_own_compartment():
    p = plane_naming(5, [], {"horns": run.HORNS}, "lateral")
    assert run.joint_answers(p, False) == {"horns:lateral_meniscus"}
    notch = plane_naming(5, [], {"horns": run.HORNS}, None)
    assert run.joint_answers(notch, False) == {"horns:meniscus"}
    empty = plane_naming(5, [], {"horns": "abstain_no_thick_low_signal_in_the_joint"})
    assert run.joint_answers(empty, False) == set()


def test_the_middle_slice_answers_by_the_bootstraps_own_naming_and_an_unread_plane_nothing():
    middle = np.zeros(SHAPE, np.int8)
    middle[0, 0:3] = A.OBJECT_CODES["lateral_meniscus"]
    boot = plane_naming(2, [], middle=True)
    assert run.joint_answers(boot, True, middle) == {"body:lateral_meniscus"}
    unreadable = run.JointPlane(
        6,
        False,
        "unreadable_geometry",
        {},
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
    assert run.joint_answers(unreadable, True) == set()


# -- the profile, partial and merged ---------------------------------------------------------------
def fake_profile(names, values, visit=None):
    """A JointProfile over DEPTH slices with `values[q]` as each quantity's area where read."""
    seen = np.ones(DEPTH, bool) if visit is None else np.asarray(visit, bool)
    status, area = {}, {}
    for q in names:
        v = np.asarray(values.get(q, np.zeros(DEPTH)), float)
        area[q] = np.where(seen, v, np.nan)
        status[q] = np.where(
            seen,
            np.where(v > 0, run.JOINT_BODY, run.JOINT_NONE),
            run.JOINT_NOT_READ,
        ).astype(np.int8)
    return run.JointProfile(
        tuple(names),
        status,
        area,
        np.where(seen, 4, -1).astype(np.int32),
        np.where(seen, 0, -1).astype(np.int32),
        np.where(seen, 9, 0).astype(np.int32),
        np.zeros((DEPTH, 1, 1), bool),
        {q: np.zeros((DEPTH, 1, 1), bool) for q in names},
        np.full((DEPTH, 4), -1, np.int32),
        np.full((DEPTH, 2), np.nan),
        np.full((DEPTH, 2), -1, np.int32),
        (),
        {q: (0.0, 1.0) for q in names},
    )


def test_a_merge_takes_each_slice_from_the_profile_that_read_it_and_keeps_unknowns():
    names = (DARK, BRIGHT)
    first = fake_profile(
        names, {DARK: np.arange(DEPTH) + 1.0}, visit=np.arange(DEPTH) < 4
    )
    rest = np.arange(DEPTH) >= 8
    second = fake_profile(names, {DARK: np.arange(DEPTH) + 100.0}, visit=rest)
    merged = run.merge_joint_profiles(first, second, rest)
    area = merged.area_mm2[DARK]
    assert area[:4].tolist() == [1.0, 2.0, 3.0, 4.0]
    assert area[8:].tolist() == [108.0, 109.0, 110.0, 111.0]
    assert np.isnan(area[4:8]).all()  # read by neither: unknown, never empty
    assert (merged.status[DARK][4:8] == run.JOINT_NOT_READ).all()
    assert (
        merged.seen_blocks[:4].tolist() == [4] * 4
        and (merged.seen_blocks[4:8] == -1).all()
    )


def test_joint_profile_visits_only_the_slices_asked_and_never_counts_the_rest_as_empty(
    monkeypatch,
):
    frame = PlaneFrame(
        np.zeros(3), np.array([[0.0, 0.0], [0.0, 1.5], [-1.5, 0.0]]), (1.5, 1.5)
    )
    monkeypatch.setattr(run, "plane_frame", lambda s, z: frame)
    monkeypatch.setattr(
        run,
        "seen_native",
        lambda s, z, n="x": (np.full(SHAPE, 50.0), np.zeros(SHAPE, bool)),
    )
    bounds = np.array([[[0, 6, 0, 6], [0, 6, 6, 12]], [[6, 12, 0, 6], [6, 12, 6, 12]]])
    stack = SimpleNamespace(
        median=np.zeros((DEPTH, 2, 2)),
        minimum=np.full((DEPTH, 2, 2), 40.0),
        maximum=np.full((DEPTH, 2, 2), 60.0),
        bounds_rc=bounds,
    )
    reach = np.zeros(SHAPE, bool)
    reach[3:9, 3:9] = True
    visit = np.zeros(DEPTH, bool)
    visit[[2, 3]] = True
    with computing(), recording() as led:
        got = run.joint_profile(
            cast(Any, SimpleNamespace(row=SimpleNamespace(series_uid="v"))),
            cast(Any, stack),
            np.empty((0, 3)),
            np.empty((0, 3)),
            {DARK: (0.0, 100.0)},
            (DARK,),
            lambda z, f, s: reach,
            "recess",
            None,
            visit,
        )
    assert (
        got.status[DARK][2] == run.JOINT_BODY and got.status[DARK][3] == run.JOINT_BODY
    )
    others = np.delete(np.arange(DEPTH), [2, 3])
    assert (got.status[DARK][others] == run.JOINT_NOT_READ).all()
    assert np.isnan(got.area_mm2[DARK][others]).all()
    counts = {e.name: e.counts["planes"] for e in led.events() if "planes" in e.counts}
    assert counts["recess.slices_not_visited"] == DEPTH - 2
    assert counts.get("recess.slices_without_both_bones_identified", 0) == 0


# -- the window ---------------------------------------------------------------------------------
def coronal_frame():
    # rows toward the feet, columns toward the left: the normal runs along y (front to back)
    return PlaneFrame(
        np.zeros(3), np.array([[0.0, 1.5], [0.0, 0.0], [-1.5, 0.0]]), (1.5, 1.5)
    )


def reference_at(y, spread=0.0, series="ref"):
    support = np.array([[0.0, y + spread * k, 0.0] for k in (-1, 0, 1)])
    return Reference(
        series,
        ("Sagittal", "0", "0"),
        "tibia",
        (4,),
        100.0,
        support,
        np.array([0.0, y, 0.0]),
        X,
        3.0,
        "R",
        "test",
        (),
    )


def view(knee="R", fat="1", positions=None, coronal=True):
    places = [3.0 * k for k in range(DEPTH)] if positions is None else positions
    objects = np.zeros(SHAPE, np.int8)
    objects[0:2] = A.OBJECT_CODES["femur"]
    objects[8:10] = A.OBJECT_CODES["tibia"]
    frame = coronal_frame()
    if not coronal:
        frame = PlaneFrame(
            np.zeros(3), np.array([[0.0, 0.0], [0.0, 1.5], [-1.5, 0.0]]), (1.5, 1.5)
        )
    axis = 1 if coronal else 0
    return SimpleNamespace(
        series=SimpleNamespace(
            row=SimpleNamespace(
                series_uid="j", fat_suppression=fat, fluid_sensitive=fat
            ),
            volume=[np.full(SHAPE, 100.0)] * DEPTH,
            geometry=SimpleNamespace(position=[np.eye(3)[axis] * p for p in places]),
            slice_thickness_mm=tuple([3.0] * DEPTH),
        ),
        record={
            "series_uid": "j",
            "slice_index": 0,
            "background_split": 1.0,
            "assignments": {
                "femur": 1,
                "tibia": 2,
                "codes": {},
                "knee": knee,
            },
            "view": ["Coronal" if coronal else "Sagittal", "1", fat],
        },
        arrays={
            "a1_objects": objects,
            "acquired_plane": np.full(SHAPE, 100.0),
        },
        assignment=SimpleNamespace(in_plane=(coronal, not coronal, True)),
        stack=SimpleNamespace(code="present"),
        frame=frame,
    )


def test_a_range_wired_for_every_question_gives_a_physical_window_with_the_middle_slice(
    monkeypatch,
):
    for q in (DARK, BRIGHT):
        monkeypatch.setitem(
            JOINT_FROM_REFERENCE_MM,
            (q, "Coronal", "1", "in_plane", "posterior"),
            (-4.0, 4.0),
        )
    own = cast(Any, view())
    # the reference's support spreads along y (a sagittal plane under a coronal stack): a landmark
    window, said = run.joint_neighbourhood(
        own, reference_at(10.0, spread=20.0), (DARK, BRIGHT), True
    )
    assert window is not None and said["code"] == "window"
    assert said["reference_kind"] == "in_plane" and said["convention"] == "posterior"
    assert np.flatnonzero(window).tolist() == [
        0,
        2,
        3,
        4,
    ]  # slice 0 is the middle slice
    # the same slices stored the other way round: the same physical places
    back = cast(Any, view(positions=[33.0 - 3.0 * k for k in range(DEPTH)]))
    back.frame = PlaneFrame(
        np.zeros(3), np.array([[0.0, -1.5], [0.0, 0.0], [-1.5, 0.0]]), (1.5, 1.5)
    )
    other, _ = run.joint_neighbourhood(
        back, reference_at(10.0, spread=20.0), (DARK, BRIGHT), True
    )
    assert other is not None
    assert sorted(33.0 - 3.0 * k for k in np.flatnonzero(other) if k) == [
        6.0,
        9.0,
        12.0,
    ]


def test_a_question_with_no_supported_range_or_any_unknown_gives_no_window_and_says_why(
    monkeypatch,
):
    own = cast(Any, view())
    window, said = run.joint_neighbourhood(own, reference_at(10.0), (DARK,), True)
    assert window is None and said["code"] == "no_supported_cohort_range_for_a_question"
    assert said["quantity_without_range"] == DARK and said["convention"] == "posterior"
    assert run.joint_neighbourhood(own, "no_confirmed_key_plane", (DARK,), True) == (
        None,
        {"code": "no_reference_no_confirmed_key_plane"},
    )
    monkeypatch.setitem(
        JOINT_FROM_REFERENCE_MM,
        (DARK, "Coronal", "1", "depth", "posterior"),
        (-4.0, 4.0),
    )
    nan_places = [3.0 * k for k in range(DEPTH)]
    nan_places[5] = float("nan")
    unsound, said = run.joint_neighbourhood(
        cast(Any, view(positions=nan_places)), reference_at(10.0), (DARK,), True
    )
    assert unsound is None and "unsound" in said["code"]
    axial = view()
    axial.frame = PlaneFrame(
        np.zeros(3), np.array([[1.5, 0.0], [0.0, 1.5], [0.0, 0.0]]), (1.5, 1.5)
    )
    none, said = run.joint_neighbourhood(
        cast(Any, axial), reference_at(10.0), (DARK,), True
    )
    assert none is None and said["code"] == "no_measured_offsets_on_this_axis"


# -- the search ---------------------------------------------------------------------------------
class World:
    """read_joint with the cheap profile and the planes' naming given: `values[q]` the areas
    through depth (the profile reads only the slices it is asked to), `names[z]` the objects plane
    z names, `codes[z]` its rule codes."""

    def __init__(
        self, monkeypatch, values, names, coronal=True, fat="1", knee="R", codes=None
    ):
        self.values, self.named, self.codes = values, names, codes or {}
        self.profile_calls: list[np.ndarray | None] = []
        self.asked: list[int] = []
        self.own = view(knee=knee, fat=fat, coronal=coronal)
        monkeypatch.setattr(run, "plane_frame", lambda s, z: self.own.frame)
        monkeypatch.setattr(
            run, "measures_of", lambda *a: SimpleNamespace(light=lambda mask: 100.0)
        )
        monkeypatch.setattr(run, "bones_identified_at", lambda o, p: set(range(DEPTH)))
        monkeypatch.setattr(run, "joint_profile", self.profile)
        monkeypatch.setattr(run, "joint_plane", self.plane)
        monkeypatch.setattr(run, "joint_twin", lambda *a: None)
        self.leg = SimpleNamespace(
            femur_lps=np.zeros((3, 3)),
            tibia_lps=np.zeros((3, 3)),
            notch_origin_lps=None,
            notch_normal=None,
        )

    def profile(self, series, stack, fem, tib, level, names, *a, visit=None, **k):
        self.profile_calls.append(None if visit is None else np.asarray(visit).copy())
        return fake_profile(names, self.values, visit)

    def plane(self, own, z, fem, tib, keys, asked, left):
        self.asked.append(z)
        names = self.named.get(z, [])
        codes = {"meniscus": "abstain_no_thick_low_signal_in_the_joint"}
        if any("meniscus" in n for n in names):
            codes["meniscus"] = "identified"
        if any("cartilage" in n for n in names):
            codes["cartilage"] = "identified"
        return plane_naming(z, names, {**codes, **self.codes.get(z, {})}, None)

    def read(self, reference="none"):
        with computing(), recording() as led:
            got = run.read_joint(
                cast(Any, self.own), None, cast(Any, self.leg), reference
            )
        assert isinstance(got, run.JointRead)
        self.led = led
        return got


def both_menisci_and_cartilage(*zs):
    return {
        z: [
            "medial_meniscus",
            "lateral_meniscus",
            "femoral_cartilage",
            "tibial_cartilage",
        ]
        for z in zs
    }


def test_the_strongest_run_is_asked_first_and_the_rest_stay_pointers_once_every_question_is_answered(
    monkeypatch,
):
    area = np.zeros(DEPTH)
    area[3], area[9] = 50.0, 90.0
    w = World(monkeypatch, {DARK: area, BRIGHT: area}, both_menisci_and_cartilage(3, 9))
    got = w.read()
    assert w.asked == [9]  # the strongest run answers all: the weaker stays a pointer
    assert got.record["search"]["stopped"].startswith("every_question_was_answered")
    assert got.record["search"]["planes_the_profile_pointed_to"] == [3, 9]
    runs = got.record["quantities"][DARK]["pointer_runs"]
    assert [r["native_rule"] for r in runs] == [
        "not_read_natively",
        "confirmed_by_the_native_rule",
    ]
    assert (
        got.record["search"]["questions"]["body:lateral_meniscus"]["answered_on_slice"]
        == 9
    )


def test_one_confirmed_meniscus_does_not_stop_the_other_sides_question(monkeypatch):
    area = np.zeros(DEPTH)
    area[3], area[6], area[9] = 90.0, 70.0, 50.0
    named = {
        3: ["medial_meniscus"],
        6: ["medial_meniscus", "tibial_cartilage", "femoral_cartilage"],
        9: ["lateral_meniscus"],
    }
    w = World(monkeypatch, {DARK: area, BRIGHT: area}, named)
    got = w.read()
    # slice 6 answers the cartilage and the medial side again, so the lateral question keeps going
    assert w.asked == [3, 6, 9]
    assert (
        got.record["search"]["questions"]["body:lateral_meniscus"]["answered_on_slice"]
        == 9
    )
    # the two sides answered on different planes, as the sided record keeps them apart
    medial = got.record["search"]["questions"]["body:medial_meniscus"][
        "answered_on_slice"
    ]
    assert medial == 3


def test_a_quantity_no_question_names_on_the_view_is_asked_nothing(monkeypatch):
    dark, fluid = np.zeros(DEPTH), np.zeros(DEPTH)
    dark[4], fluid[8] = (
        60.0,
        200.0,
    )  # the stronger fluid run points at a plane the ACL gate refuses
    w = World(
        monkeypatch,
        {DARK: dark, BRIGHT: np.zeros(DEPTH), FLUID: fluid},
        {
            4: [
                "medial_meniscus",
                "lateral_meniscus",
                "femoral_cartilage",
                "tibial_cartilage",
            ]
        },
    )
    got = w.read()
    assert w.asked == [4]
    assert got.record["search"]["quantities_with_no_question_on_this_view"] == [FLUID]
    # the pointer is kept and says it was not read natively: a pointer, not an absence
    assert (
        got.record["quantities"][FLUID]["pointer_runs"][0]["native_rule"]
        == "not_read_natively"
    )
    assert 8 in got.record["search"]["planes_the_profile_pointed_to"]


def test_a_tie_is_never_broken_and_a_plateau_is_asked_at_every_slice(monkeypatch):
    area = np.zeros(DEPTH)
    area[2:4] = 80.0  # a plateau of two slices
    area[7] = 80.0  # a second run of equal support
    w = World(monkeypatch, {DARK: area, BRIGHT: np.zeros(DEPTH)}, {}, knee="")
    w.read()
    assert sorted(w.asked) == [
        2,
        3,
        7,
    ]  # nothing named: every tied slice of every tied run


def test_a_plane_pointed_to_by_two_quantities_is_read_once(monkeypatch):
    both = np.zeros(DEPTH)
    both[5] = 70.0
    w = World(monkeypatch, {DARK: both, BRIGHT: both}, {})
    got = w.read()
    assert w.asked == [5]
    row = next(p for p in got.record["pointed_planes"] if p["slice"] == 5)
    assert sorted(row["pointed_by"]) == [BRIGHT, DARK]


def with_window(monkeypatch, lo=-4.0, hi=4.0):
    for q in (DARK, BRIGHT):
        monkeypatch.setitem(
            JOINT_FROM_REFERENCE_MM,
            (q, "Coronal", "1", "in_plane", "posterior"),
            (lo, hi),
        )


def test_the_expected_neighbourhood_is_read_first_and_the_stronger_run_beyond_stays_unknown(
    monkeypatch,
):
    with_window(monkeypatch)
    area = np.zeros(DEPTH)
    area[3], area[9] = 50.0, 200.0
    w = World(monkeypatch, {DARK: area, BRIGHT: area}, both_menisci_and_cartilage(3, 9))
    got = w.read(reference_at(10.0, spread=20.0))
    search = got.record["search"]
    assert search["code"] == "window" and w.asked == [3]
    assert not search["broadened_to_the_whole_established_depth"]
    assert len(w.profile_calls) == 1 and w.profile_calls[0] is not None
    # the run beyond the window was never visited: unknown, never empty
    assert np.isnan(got.arrays["a3_joint_dark_area_mm2"][9])
    assert got.arrays["a3_joint_dark_status"][9] == run.JOINT_NOT_READ
    assert not got.arrays["a3_joint_search_visited"].all()
    assert (
        "slices_outside_the_expected_neighbourhood_were_not_visited_unknown_not_empty"
        in got.record["ambiguities"]
    )


def test_an_unanswered_question_broadens_by_merge_without_rereading_a_slice_or_a_plane(
    monkeypatch,
):
    with_window(monkeypatch)
    area = np.zeros(DEPTH)
    area[3], area[9] = 50.0, 200.0
    named = {
        3: ["medial_meniscus"],
        9: ["lateral_meniscus", "femoral_cartilage", "tibial_cartilage"],
    }
    w = World(monkeypatch, {DARK: area, BRIGHT: area}, named)
    got = w.read(reference_at(10.0, spread=20.0))
    assert got.record["search"]["broadened_to_the_whole_established_depth"]
    first, second = w.profile_calls
    assert first is not None and second is not None
    assert not (first & second).any()  # no slice's cheap profile read twice
    assert w.asked == [3, 9] and len(set(w.asked)) == 2  # no plane asked twice
    assert got.arrays["a3_joint_search_visited"].all()
    assert got.arrays["a3_joint_dark_area_mm2"][9] == 200.0


def test_a_run_still_rising_at_the_window_edge_is_walked_to_its_own_peak(monkeypatch):
    with_window(monkeypatch)
    rising = np.zeros(DEPTH)
    rising[3:8] = [
        10.0,
        20.0,
        30.0,
        40.0,
        30.0,
    ]  # window covers slices 0, 2-4: peak at 6
    w = World(
        monkeypatch,
        {DARK: rising, BRIGHT: np.zeros(DEPTH)},
        both_menisci_and_cartilage(6),
        fat="1",
    )
    got = w.read(reference_at(10.0, spread=20.0))
    assert w.asked == [6]  # the run's own representative, not the window's edge
    walked = sum(
        e.counts["planes"] for e in w.led.events() if e.name == "joint.walked_slices"
    )
    assert (
        walked == 3
    )  # slices 5, 6 and 7: the peak and the slice beyond it that shows it is one
    assert not got.record["search"]["broadened_to_the_whole_established_depth"]


def test_no_reference_reads_the_established_depth_in_one_pass_with_the_reason(
    monkeypatch,
):
    area = np.zeros(DEPTH)
    area[5] = 70.0
    w = World(monkeypatch, {DARK: area, BRIGHT: area}, {})
    got = w.read("no_confirmed_key_plane")
    assert got.record["search"]["code"] == "no_reference_no_confirmed_key_plane"
    assert got.record["search"]["passes"] == 1 and w.profile_calls[0] is None
    assert got.arrays["a3_joint_search_window"].all()


def test_the_rows_the_recess_family_reads_stay_aligned_with_the_planes_read(
    monkeypatch,
):
    area = np.zeros(DEPTH)
    area[3], area[9] = 50.0, 90.0
    w = World(monkeypatch, {DARK: area, BRIGHT: area}, {3: ["medial_meniscus"], 9: []})
    got = w.read()
    rows = [p for p in got.record["pointed_planes"] if not p["middle"]]
    assert [p["slice"] for p in rows] == sorted(w.asked)
    assert got.arrays["a3_joint_plane_objects"].shape[0] == len(rows)
    assert got.arrays["a3_joint_plane_slices"].tolist() == [p["slice"] for p in rows]
    first = got.arrays["a3_joint_plane_objects"][0]
    assert (
        first == A.OBJECT_CODES["medial_meniscus"]
    ).any()  # row 0 is slice 3's naming
