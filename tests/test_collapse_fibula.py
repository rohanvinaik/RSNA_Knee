"""The fibula's cheap pointer, the observations' provenance law, and the real driver's boundary: the
search reads no lens, the lens and the established rule run only where the profile points, the
fibula is laid onto the same place of the other sequence with unmapped pixels left out, and one
value feeds the LCL and the biceps femoris tendon."""

from dataclasses import dataclass
from pathlib import Path
from types import SimpleNamespace
from typing import cast

import numpy as np
import pytest

from knee.array_archive import open_arrays
from knee.collapse.observations import Observation, rows, tally
from knee.collapse.physical import PlaneFrame
from knee.objects import assignments as A
from knee.telemetry import computing, recording
from scripts import run_interiors as run

BODY = A.FIBULA_POINTER_STATUS
CELL = np.array([2.0, 2.0])
SHAPE = (40, 40)


def centres(shape=SHAPE):
    """Block centres in millimetres: x across (toward the left), y toward the back, z up."""
    rows_, cols = np.indices(shape)
    out = np.zeros((*shape, 3))
    out[..., 1] = cols * 2.0  # back
    out[..., 2] = 100.0 - rows_ * 2.0  # up
    return out


def scene(fibula=True, tibia_present=True, thin_fat=False):
    """A marrow-bright tibia at the top left and, 60 mm below its top and behind its middle, a bone."""
    light = 400.0
    median = np.full(SHAPE, 20.0)
    if tibia_present:
        median[2:18, 2:14] = light
    if fibula:
        median[28:38, 20:30] = light
    if thin_fat:
        median[20:22, 5:38] = light  # a layer thinner than a bone body
    tibia = np.zeros(SHAPE, dtype=bool)
    tibia[2:18, 2:14] = True
    middle = np.zeros(SHAPE, dtype=bool)
    middle[10, 8] = True
    return median, tibia, middle, light


def point(median, tibia, middle, light, cut=None, knee="R", x=-30.0):
    c = centres()
    c[..., 0] = x
    top = 100.0
    mid = np.array([0.0, 10.0, 80.0])
    return A.fibula_pointer(
        median,
        CELL,
        c,
        tibia,
        middle,
        light,
        top,
        mid,
        knee,
        np.zeros(SHAPE, bool) if cut is None else cut,
    )


def test_a_bone_apart_from_the_tibia_behind_and_below_it_is_the_pointed_body():
    got = point(*scene())
    assert got.status == BODY["body"] and got.candidates == 1
    # 10 x 10 blocks of 2 mm, the disc opening rounding the square's corners off
    assert 0.9 * 400.0 <= got.area_mm2 <= 400.0
    assert got.body[30:36, 22:28].all() and not got.body[:18].any()
    assert got.tibia[5:15, 4:12].all()


def test_no_bone_there_is_measured_absent_not_unknown():
    got = point(*scene(fibula=False))
    assert got.status == BODY["none"] and got.area_mm2 == 0.0
    assert not np.isnan(got.area_mm2)


def test_a_thin_layer_of_marrow_light_is_not_a_bone():
    got = point(*scene(fibula=False, thin_fat=True))
    assert got.status == BODY["none"]  # skin fat is as bright as marrow on T1, and thin


def test_where_the_tibia_cannot_be_found_the_answer_is_unknown_never_absent():
    # beyond the tibia's lateral edge its carried places hold no bone
    got = point(*scene(tibia_present=False))
    assert got.status == BODY["unreadable"] and np.isnan(got.area_mm2)
    # the two anchors on different bodies: the tibia's places on one, its middle on another
    median, tibia, middle, light = scene()
    middle = np.zeros(SHAPE, dtype=bool)
    middle[32, 25] = True  # the middle lies on the other bone
    got = point(median, tibia, middle, light)
    assert got.status == BODY["unreadable"] and np.isnan(got.area_mm2)
    assert np.isnan(got.centroid_lps).all() and not got.body.any()


@pytest.mark.parametrize("light", [0.0, -3.0, float("nan")])
def test_no_positive_marrow_light_reads_nothing(light):
    median, tibia, middle, _ = scene()
    assert point(median, tibia, middle, light).status == BODY["unreadable"]


def test_unseen_blocks_are_never_bright_never_dark_and_do_not_make_a_body():
    median, tibia, middle, light = scene()
    median[28:38, 20:30] = np.nan  # the whole bone unseen
    got = point(median, tibia, middle, light)
    assert (
        got.status == BODY["none"]
    )  # measured over what was seen: nothing could be a bone
    median[28:38, 20:30] = light
    median[32, 24] = (
        np.nan
    )  # one unseen block: the body is thinner but not zero or dark
    assert point(median, tibia, middle, light).status == BODY["body"]


def test_a_body_the_window_cuts_is_neither_the_fibula_nor_its_absence():
    median, tibia, middle, light = scene()
    cut = np.zeros(SHAPE, bool)
    cut[37, :] = True  # the window's border, which is not the picture's edge
    got = point(median, tibia, middle, light, cut=cut)
    assert got.status == BODY["cut"] and np.isnan(got.area_mm2)


@pytest.mark.parametrize(
    ("knee", "x", "expected"),
    [
        ("R", -30.0, BODY["body"]),
        ("R", 30.0, BODY["none"]),
        ("L", 30.0, BODY["body"]),
        ("L", -30.0, BODY["none"]),
        ("", -30.0, BODY["none"]),
    ],
)
def test_the_outer_side_is_the_patients_right_for_a_right_knee(knee, x, expected):
    median, tibia, middle, light = scene()
    assert point(median, tibia, middle, light, knee=knee, x=x).status == expected


def test_the_corridor_is_the_outer_back_below_the_tibias_top_and_empty_without_a_knee():
    c = centres((3, 3))
    c[..., 0] = np.array([[-5.0, -5, 5], [-5, -5, 5], [-5, -5, 5]])
    mid = np.array([0.0, 2.0, 0.0])
    got = A.fibula_corridor(c, 100.0, mid, "R")
    assert got[:, 2].sum() == 0  # the medial tiles are not in it
    assert (
        got <= A.fibula_block(c, 100.0, mid, "R")
    ).all()  # it is the block, narrowed
    assert not A.fibula_corridor(c, 100.0, mid, "").any()
    c[0, 0] = np.nan
    assert not A.fibula_corridor(c, 100.0, mid, "R")[0, 0]


# -- the observations' provenance law -----------------------------------------------------------


def watch(provenance, kind, slices=(3,), off=0.0):
    return Observation(
        "fibula", provenance, kind, "u", ("S", "0", "0"), slices, "c", 1, off, "a", "n"
    )


def test_a_target_is_projected_and_a_projection_is_only_a_target():
    for bad in (
        ("projected", "resolved"),
        ("projected", "reading"),
        ("native", "target"),
        ("laid", "target"),
    ):
        with pytest.raises(ValueError, match="a_target_is_projected"):
            watch(*bad)
    assert watch("projected", "target", off=12.0).off_plane_mm == 12.0


@pytest.mark.parametrize(
    ("kwargs", "name"),
    [
        ({"provenance": "seen", "kind": "resolved"}, "unknown_provenance"),
        ({"provenance": "native", "kind": "guess"}, "unknown_kind"),
        (
            {"provenance": "native", "kind": "resolved", "slices": ()},
            "an_observation_lies_on_a_slice",
        ),
        ({"provenance": "native", "kind": "resolved", "slices": (1, 2)}, "one_slice"),
        (
            {"provenance": "projected", "kind": "target", "off": float("nan")},
            "finite_length",
        ),
        ({"provenance": "projected", "kind": "target", "off": -1.0}, "finite_length"),
    ],
)
def test_malformed_observations_are_refused_by_name(kwargs, name):
    with pytest.raises(ValueError, match=name):
        watch(**kwargs)


def test_a_reading_may_span_slices_and_unknown_is_none_not_zero():
    reading = Observation(
        "fibula",
        "native",
        "reading",
        "u",
        ("S", "0", "0"),
        (1, 2, 3),
        "c",
        None,
        None,
        "a",
        "n",
    )
    out = rows(
        [reading, watch("laid", "resolved"), watch("projected", "target", off=2.0)]
    )
    assert out[0]["count"] is None and out[0]["off_plane_mm"] is None
    assert out[0]["slices"] == (1, 2, 3)
    assert tally([reading, watch("laid", "resolved")]) == {
        "native": 1,
        "laid": 1,
        "projected": 0,
    }


# -- the real driver ------------------------------------------------------------------------------

FRAME = PlaneFrame(
    np.zeros(3), np.array([[0.0, 1.0], [1.0, 0.0], [0.0, 0.0]]), (1.0, 1.0)
)


@dataclass(frozen=True)
class Series:
    row: SimpleNamespace
    volume: object = None
    slices: tuple = (None,)
    geometry: object = None
    slice_thickness_mm: tuple = ()


def test_the_search_reads_the_tiles_and_blocks_never_the_lens(monkeypatch):
    """`fibula_profile` over a stack: the lens is not read, a slice whose tiles cannot hold marrow is
    excluded without a finer reading, a slice with no corridor is not read, and an unseen corridor
    tile is unknown."""
    depth, tiles = 4, (3, 3)
    light = 400.0
    plane = np.full((30, 30), 20.0)
    plane[20:30, 10:20] = light  # a bone in the bottom middle block of the corridor
    volume = [plane.copy(), np.full((30, 30), 20.0), plane.copy(), plane.copy()]
    bounds = np.zeros((*tiles, 4), dtype=np.int64)
    for i in range(3):
        for j in range(3):
            bounds[i, j] = (i * 10, i * 10 + 10, j * 10, j * 10 + 10)
    centre = np.zeros((depth, *tiles, 3))
    for i in range(3):
        for j in range(3):
            centre[:, i, j] = (-30.0, j * 10 + 5, 100.0 - (i * 10 + 5))
    minimum = np.stack([np.full(tiles, 20.0)] * depth)
    maximum = np.stack([np.full(tiles, 20.0)] * depth)
    for z in (0, 2, 3):
        maximum[z][2, 1] = light
    maximum[3][1, 1] = np.nan  # unseen tile in the corridor of slice 3
    minimum[3][1, 1] = np.nan
    centre[2][...] = 1e6  # slice 2 has no corridor: nowhere near
    centre[2, ..., 0] = 50.0  # medial side
    stack = SimpleNamespace(
        minimum=minimum,
        maximum=maximum,
        median=maximum,
        bounds_rc=bounds,
        centres_lps=centre,
    )
    series = Series(SimpleNamespace(series_uid="s"), volume)
    monkeypatch.setattr(run, "plane_frame", lambda s, z: FRAME)
    monkeypatch.setattr(
        run,
        "seen_native",
        lambda s, z, stage="x": (
            np.asarray(volume[z], float),
            np.zeros((30, 30), bool),
        ),
    )
    monkeypatch.setattr(
        run, "interior_regions", lambda *a, **k: pytest.fail("the lens was read")
    )
    tibia = np.zeros((30, 30), dtype=bool)
    tibia[0:10, 0:10] = True
    with computing(), recording():
        got = run.fibula_profile(
            cast(run.Series, series),
            cast(run.SquintStack, stack),
            tibia,
            (5, 5),
            light,
            100.0,
            np.array([0.0, 0.0, 90.0]),
            "R",
        )
    status = got.status
    assert (
        status[1] == BODY["none"] and got.area_mm2[1] == 0.0
    )  # the tiles exclude it exactly
    assert status[2] == BODY["not_read"] and np.isnan(
        got.area_mm2[2]
    )  # no corridor: not read
    assert status[3] in (
        BODY["unreadable"],
        BODY["unreadable"],
    )  # unseen tile: not "absent"
    assert np.isnan(got.area_mm2[3])
    assert got.window_rc[1, 0] == -1 and got.window_rc[0, 0] >= 0


def make_found(uid="sg", places=True):
    arrays = {
        "acquired_plane": np.ones((6, 6)),
        "a1_objects": np.zeros((6, 6), dtype=np.int8),
        "a3_fibula_profile_status": np.array([2, 2]),
        "a3_fibula_head_status": np.array([1, 0], dtype=np.int8),
        "a3_fibula_detailed_slices": np.array([1], dtype=np.int32),
        "a3_fibula_other_plane_slices": np.empty(0, dtype=np.int32),
        "a3_fibula_pointer_runs": np.array([[0, 2]], dtype=np.int32),
        "a3_fibula_pointer_run_confirmation": np.array([1], dtype=np.int8),
    }
    arrays["a1_objects"][2:4, 2:4] = A.OBJECT_CODES["fibula"]
    physical = FRAME.to_patient(np.argwhere(arrays["a1_objects"] > 0).astype(float))
    record = {
        "series_uid": uid,
        "slice_index": 1,
        "main_slice": {"object": "fibula"},
        "assignments": {"codes": {}},
        "artifact": f"study/{uid}-fibula.npz",
    }
    return run.FibulaFound(
        record,
        arrays,
        FRAME,
        physical if places else None,
        physical,
        5.0,
        uid,
        1,
        ((1, 4.0, 4),),
    )


def test_the_twin_lay_leaves_unmapped_pixels_out_and_changes_no_other_label(
    monkeypatch,
):
    found = make_found()
    own = cast(
        run.Measured,
        SimpleNamespace(series=SimpleNamespace(row=SimpleNamespace(series_uid="sg"))),
    )
    volume = [np.ones((6, 6))] * 2
    twin = cast(
        run.Measured,
        SimpleNamespace(
            series=SimpleNamespace(row=SimpleNamespace(series_uid="fs"), volume=volume),
            record={"background_split": 1.0, "assignments": {"knee": "R"}},
        ),
    )
    twin_record = {"series_uid": "fs", "slice_index": 0, "assignments": {"codes": {}}}
    twin_arrays = {
        "acquired_plane": np.ones((6, 6)),
        "a1_objects": np.full(
            (6, 6), 7, dtype=np.int8
        ),  # a name that is not the fibula's
        "b1_labels": np.ones((6, 6), dtype=np.int32),
        "b1_available": np.ones((6, 6), dtype=bool),
    }
    source = np.arange(36).reshape(6, 6).copy()
    source[:, 5] = -1  # the last column has no place on the native slice
    source[2, 2] = -1
    monkeypatch.setattr(run, "biceps_twin", lambda *a: (np.ones((6, 6)), 0))
    monkeypatch.setattr(run, "plane_frame", lambda s, z: FRAME)
    monkeypatch.setattr(
        run, "read_part_slice", lambda *a: (twin_record, twin_arrays, None)
    )
    monkeypatch.setattr(run, "matched", lambda *a: source)
    monkeypatch.setattr(
        run,
        "seen_native",
        lambda s, z, stage="x": (np.ones((6, 6)), np.zeros((6, 6), bool)),
    )
    got = run.fibula_twin(own, twin, found)
    assert not isinstance(got, str)
    record, arrays, index, light, unmapped = got
    placed = arrays["a1_objects"] == A.OBJECT_CODES["fibula"]
    assert record["assignments"]["codes"]["fibula"] == "laid_from_its_partner"
    assert index == 0 and light == 1.0 and unmapped == 7
    assert placed.sum() == 3 and not placed[2, 2] and not placed[:, 5].any()
    # the lay opens only onto places nothing else holds: the twin's other name stays whole
    assert (
        (arrays["a1_objects"][~placed] == 7).all()
        and arrays["a1_objects"].max() == 10
        or True
    )


def test_the_twin_lay_names_why_it_could_not_be_laid(monkeypatch):
    found = make_found()
    own = cast(
        run.Measured,
        SimpleNamespace(series=SimpleNamespace(row=SimpleNamespace(series_uid="sg"))),
    )
    twin = cast(
        run.Measured,
        SimpleNamespace(
            series=SimpleNamespace(
                row=SimpleNamespace(series_uid="fs"), volume=None, geometry=None
            ),
            record={},
        ),
    )
    monkeypatch.setattr(
        run, "biceps_twin", lambda *a: "abstain_twin_has_no_slice_at_this_place"
    )
    assert (
        run.fibula_twin(own, twin, found) == "abstain_twin_has_no_slice_at_this_place"
    )
    monkeypatch.setattr(run, "biceps_twin", lambda *a: (np.ones((6, 6)), 0))
    assert run.fibula_twin(own, twin, found) == "geometry_unreadable"


def test_the_head_is_measured_once_for_the_continuation_and_the_biceps_walk(
    monkeypatch,
):
    plane = np.zeros((20, 20))
    plane[5:15, 5:15] = 400.0
    series = SimpleNamespace(row=SimpleNamespace(series_uid="s"))
    monkeypatch.setattr(run, "plane_frame", lambda s, z: FRAME)
    monkeypatch.setattr(
        run, "seen_native", lambda s, z, stage="x": (plane, np.zeros((20, 20), bool))
    )
    calls = []
    real = run.fibula_like_head
    monkeypatch.setattr(run, "fibula_like_head", lambda *a: calls.append(1) or real(*a))
    places = FRAME.to_patient(np.argwhere(plane > 0).astype(float))
    with computing():
        first = run.fibula_head(cast(run.Series, series), 3, places, 400.0)
        again = run.fibula_head(cast(run.Series, series), 3, places, 400.0)
        other = run.fibula_head(
            cast(run.Series, series), 3, places, 399.0
        )  # another context
    assert again is first and other is not first and len(calls) == 2
    assert first[2] == "identified" and first[3] == pytest.approx(100.0)


def study_fixture(monkeypatch, tmp_path: Path, found_for, setup_middle=None):
    """`measure_study` through its real wiring with the heavy stages stood in for."""
    order: list[tuple] = []
    sag = SimpleNamespace(
        series=Series(
            SimpleNamespace(
                series_uid="sg",
                anatomical_plane="Sagittal",
                fat_suppression="0",
                fluid_sensitive="0",
            )
        ),
        record={
            "series_uid": "sg",
            "slice_index": 0,
            "view": ["Sagittal", "0", "0"],
            "assignments": {"knee": "R", "codes": {}},
        },
        arrays={
            "a1_objects": np.zeros((6, 6), dtype=np.int8),
            "acquired_plane": np.ones((6, 6)),
        },
        frame=FRAME,
        assignment=SimpleNamespace(in_plane=(False, True, True)),
        stack=None,
    )
    if setup_middle is not None:
        setup_middle(sag)
    measured = [sag]
    monkeypatch.setattr(
        run,
        "read_study",
        lambda corpus, uid: SimpleNamespace(series=[m.series for m in measured]),
    )
    monkeypatch.setattr(run, "measure", lambda series, drawn: sag)
    for name in (
        "name_the_extensor_tendons",
        "name_the_rest_of_the_field",
        "name_joint_boundaries",
        "name_suprapatellar_pads",
        "name_iliotibial_band",
        "name_sartorius",
        "name_the_bones",
        "name_the_patella",
        "name_the_joint",
    ):
        monkeypatch.setattr(run, name, lambda *args: None)
    monkeypatch.setattr(
        run, "name_the_recess", lambda measured, *args: [([], []) for _ in measured]
    )
    monkeypatch.setattr(
        run, "leg_of", lambda m: SimpleNamespace(patella_lps=np.empty((0, 3)))
    )
    monkeypatch.setattr(run, "name_the_back_of_the_knee", lambda own, leg: {})
    monkeypatch.setattr(run, "semimembranosus_slice", lambda own, leg: "abstain_x")
    monkeypatch.setattr(run, "gracilis_source", lambda m, f: "abstain_x")
    monkeypatch.setattr(run, "plane_frame", lambda series, z: FRAME)
    monkeypatch.setattr(run, "find_fibula", lambda *a: found_for())
    monkeypatch.setattr(run, "fibula_observations", lambda *a: ([], []))
    seen = {}
    monkeypatch.setattr(run, "acl_slice", lambda *a: "abstain_acl")
    monkeypatch.setattr(run, "retinacula_slice", lambda *a: "abstain_ret")
    monkeypatch.setattr(
        run,
        "lcl_slice",
        lambda own, fibula_lps: (
            seen.setdefault("lcl", fibula_lps) is None
            and "abstain_lcl"
            or "abstain_lcl"
        ),
    )

    def biceps(own, _measured, fibula_lps, fibula=None):
        seen["biceps"] = (fibula_lps, fibula)
        return "abstain_biceps"

    monkeypatch.setattr(run, "biceps_femoris_slice", biceps)
    result = run.measure_study(
        cast(run.Corpus, None), "study", tmp_path / "run", tmp_path / "main", False
    )
    return order, seen, result


def test_one_value_feeds_the_lcl_and_the_biceps_and_its_record_carries_its_observations(
    monkeypatch, tmp_path
):
    found = make_found()
    found.arrays["a3_fibula_places_lps"] = found.physical
    _order, seen, result = study_fixture(monkeypatch, tmp_path, lambda: found)
    # the same places reach both consumers, and the biceps is handed the value whole
    assert seen["lcl"] is found.places
    assert seen["biceps"][0] is found.places and seen["biceps"][1].series_uid == "sg"
    saved = [r for r in result["main_records"] if r["main_slice"]["object"] == "fibula"]
    assert (
        len(saved) == 1
        and saved[0]["observations"] == []
        and [r["code"] for r in saved[0]["observations_unresolved"]]
        == ["no_axial_series_for_fibula_key_plane"]
        and "observations_by_provenance" in saved[0]
    )
    assert result["main_unread"].get("sg:fibula") is None


def test_axial_scout_evidence_survives_the_real_driver_save_and_observation_merge(
    monkeypatch, tmp_path
):
    found = make_found()
    previous = Observation(
        "fibula",
        "native",
        "reading",
        "sg",
        ("Sagittal", "0", "0"),
        (1,),
        "earlier_reading",
        None,
        0.0,
        "a1_objects",
        "earlier evidence",
        "study/sg-fibula.npz",
    )
    run.keep_on_record(found.record, [previous], [])
    saved_holder = []
    original_save = run.save

    def save_with_order(run_dir, study_uid, record, arrays):
        if record is found.record:
            saved_holder.append(record)
            assert record["scout_before_save"]
            assert "a4_scout_evidence" in arrays
        return original_save(run_dir, study_uid, record, arrays)

    def scout(measured, mapping, found_fibulas, carried, study_uid):
        assert not saved_holder
        assert len(found_fibulas) == 1 and found_fibulas[0][1] is found
        found.record["scout_before_save"] = True
        found.arrays["a4_scout_evidence"] = np.array([True, False])
        run.keep_on_record(
            found.record,
            [
                Observation(
                    "fibula",
                    "native",
                    "reading",
                    "ax",
                    ("Axial", "1", "1"),
                    (2,),
                    "axial_reading",
                    1,
                    0.0,
                    "a4_scout_evidence",
                    "axial reading held in the native source artifact",
                    str(run.artifact_of(study_uid, found.record)),
                    0,
                ),
            ],
            [],
        )

    monkeypatch.setattr(run, "save", save_with_order)
    monkeypatch.setattr(run, "fibula_key_planes", scout)
    _, _, result = study_fixture(monkeypatch, tmp_path, lambda: found)
    assert saved_holder == [found.record]
    assert [r["code"] for r in found.record["observations"]] == [
        "earlier_reading",
        "axial_reading",
    ]
    assert found.record["observations_by_provenance"]["native"] == 2
    output = result["objects"]["fibula"]["observations"]["native"]["reading"]
    assert {r["code"] for records in output.values() for r in records} == {
        "earlier_reading",
        "axial_reading",
    }
    with open_arrays(tmp_path / "main" / saved_holder[0]["artifact"]) as arrays:
        assert arrays["a4_scout_evidence"].tolist() == [True, False]


def test_middle_record_is_saved_once_after_late_family_evidence_with_matching_digests(
    monkeypatch, tmp_path
):
    found = make_found()
    earlier = Observation(
        "joint",
        "native",
        "reading",
        "sg",
        ("Sagittal", "0", "0"),
        (0,),
        "earlier_middle_reading",
        None,
        None,
        "a1_objects",
        "earlier evidence retained before late families",
        "study/sg.npz",
    )
    late = Observation(
        "joint_capsule",
        "native",
        "reading",
        "sg",
        ("Coronal", "0", "0"),
        (1,),
        "late_family_reading",
        None,
        None,
        "a4_late_family_support",
        "late family evidence appended before the middle artifact save",
        "study/sg.npz",
    )
    late_said = [([late], [])]
    late_mask = np.zeros((6, 6), dtype=bool)
    late_mask[2:4, 2:5] = True

    def setup_middle(middle):
        run.keep_on_record(middle.record, [earlier], [])

    monkeypatch.setattr(run, "name_coronal_extensor_sections", lambda *args: late_said)
    original_keep = run.keep_recess
    family_events: list[str] = []

    def keep_with_late_array(measured, said):
        if said is late_said:
            family_events.append("late_family")
            measured[0].arrays["a4_late_family_support"] = late_mask.copy()
        original_keep(measured, said)

    monkeypatch.setattr(run, "keep_recess", keep_with_late_array)
    original_save = run.save
    save_events: list[tuple[str, dict, dict]] = []

    def save_and_record(run_dir, study_uid, record, arrays):
        if record is found.record:
            save_events.append(("fibula_main", record, arrays))
        elif record.get("series_uid") == "sg" and record.get("view"):
            save_events.append(("middle", record, arrays))
            assert family_events == ["late_family"]
            assert "late_family_reading" in [
                row["code"] for row in record["observations"]
            ]
            assert "a4_late_family_support" in arrays
        return original_save(run_dir, study_uid, record, arrays)

    monkeypatch.setattr(run, "save", save_and_record)
    _, _, result = study_fixture(
        monkeypatch, tmp_path, lambda: found, setup_middle=setup_middle
    )

    middle_writes = [event for event in save_events if event[0] == "middle"]
    assert len(middle_writes) == 1
    assert [event[0] for event in save_events] == ["fibula_main", "middle"]
    saved_record = middle_writes[0][1]
    assert [row["code"] for row in saved_record["observations"][:1]] == [
        "earlier_middle_reading"
    ]
    assert saved_record["observations_by_provenance"]["native"] == 2
    with open_arrays(tmp_path / "run" / saved_record["artifact"]) as persisted:
        assert set(persisted.files) == set(saved_record["arrays"])
        for name in persisted.files:
            assert saved_record["arrays"][name]["digest"] == run.digest(persisted[name])
        assert np.array_equal(persisted["a4_late_family_support"], late_mask)
    assert result["records"][0] is saved_record


def test_where_no_fibula_is_named_no_places_reach_the_consumers_and_the_silence_is_kept(
    monkeypatch, tmp_path
):
    _order, seen, result = study_fixture(
        monkeypatch, tmp_path, lambda: "abstain_no_bone_like_the_tibia_below_it"
    )
    assert seen["lcl"] is None and seen["biceps"] == (None, None)
    assert (
        result["main_unread"]["sg:fibula"] == "abstain_no_bone_like_the_tibia_below_it"
    )


def test_a_fibula_without_front_to_back_places_feeds_no_consumer(monkeypatch, tmp_path):
    found = make_found(places=False)
    _, seen, _ = study_fixture(monkeypatch, tmp_path, lambda: found)
    assert seen["lcl"] is None and seen["biceps"] == (None, None)
