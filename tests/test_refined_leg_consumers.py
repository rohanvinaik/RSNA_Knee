"""P2b increment 2: the leg refined by the bones' later native sections (`refine_leg`) reaches the two
consumers that run after it, the bones' own axial key planes (`axial_bone_planes`, inside
`build_study_map`) and the fibula's axial key plane (`fibula_key_planes`); every reader before the
bones, and every other reader after them, keeps the early leg.

`leg_on` keys a leg's projection onto a slice by the leg's identity, so a refined leg is never handed
the early leg's projection, one leg's projection is made once and handed to every consumer that asks,
an equal leg reuses it, and the readings that depend on the slice's frame alone (`coarse_axial_blocks`,
`coarse_axial_depth`) are shared by both legs. Nothing here fits a number: each case builds two legs
whose places differ and reads what the consumer decides from each.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, replace
from pathlib import Path
from types import SimpleNamespace
from typing import Any, cast

import numpy as np
import pytest

from knee.collapse.coarse_section import SECTION, SHARED
from knee.collapse.physical import PlaneFrame
from knee.collapse.study_map import StudyMap
from scripts import run_interiors as run

STUDY = "1.2.826.0.1.3680043.8.498.10095687747295410396510538520594649149"
HOLDER = "holder-sagittal"
THICKNESS = 3.0
SLICES = 3


def make_frame(origin: Sequence[float], basis: Sequence[Sequence[float]]) -> PlaneFrame:
    return PlaneFrame(np.asarray(origin), np.asarray(basis, dtype=float), (1.0, 1.0))


def axial_frame(z: float) -> PlaneFrame:
    """Row toward the patient's left, column toward the back: a place (x, y) lands on pixel (x, y)."""
    return make_frame((0.0, 0.0, z), [[1, 0], [0, 1], [0, 0]])


SAGITTAL = make_frame((30.0, 0.0, 50.0), [[0, 0], [1, 0], [0, -1]])


def ring(radius: float = 8.0) -> np.ndarray:
    """A dark marrow disc inside a dark cortex ring inside a bright rim (fat suppressed)."""
    rr, cc = np.mgrid[:64, :64]
    dist = np.hypot(rr - 30, cc - 30)
    image = np.full((64, 64), 100.0)
    image[dist <= radius] = 30.0
    image[(dist > radius) & (dist <= radius + 2)] = 5.0
    image[(dist > radius + 2) & (dist <= radius + 4)] = 200.0
    return image


@pytest.fixture(autouse=True)
def frames_of_the_stub_series(monkeypatch):
    """Each stub series carries its own frames, as the real headers would give them."""
    monkeypatch.setattr(run, "plane_frame", lambda series, z: series.frames[z])


def make_leg(
    femur: Sequence[Sequence[float]], tibia: Sequence[Sequence[float]]
) -> run.Leg:
    """A leg with its identity, as `leg_of` and `refine_leg` make one."""
    early = run.Leg(
        np.asarray(femur, dtype=float).reshape(-1, 3),
        np.asarray(tibia, dtype=float).reshape(-1, 3),
        None,
        None,
        np.zeros((0, 3)),
    )
    return replace(early, identity=run.leg_identity(early))


def axial_target(uid: str) -> Any:
    """One axial series of three slices, 3 mm apart, each with a dark marrow disc at pixel (30, 30)."""
    volume = np.stack([ring() for _ in range(SLICES)])
    series = SimpleNamespace(
        view="axial",
        row=SimpleNamespace(series_uid=uid, fat_suppression="1"),
        volume=volume,
        slice_thickness_mm=[THICKNESS] * SLICES,
        frames=[axial_frame(THICKNESS * z) for z in range(SLICES)],
    )
    return SimpleNamespace(
        series=series,
        record={
            "series_uid": uid,
            "view": ["Axial", "1", "1"],
            "observations": [],
            "assignments": {"knee": "R"},
        },
        arrays={"acquired_plane": volume[1]},
    )


def native_source(points: np.ndarray) -> tuple[Any, Any]:
    """A native sagittal fibula section, as `test_fibula_key_planes` builds one."""
    series = SimpleNamespace(
        view="sagittal",
        row=SimpleNamespace(series_uid=HOLDER, fat_suppression="0"),
        slice_thickness_mm=[THICKNESS],
        frames=[SAGITTAL],
    )
    record = {
        "series_uid": HOLDER,
        "view": ["Sagittal", "0", "0"],
        "main_slice": {"object": "fibula"},
        "observations": [],
        "observations_by_provenance": {"native": 0, "laid": 0, "projected": 0},
        "observations_unresolved": [],
    }
    own = SimpleNamespace(series=series, record=record, arrays={})
    found = SimpleNamespace(
        record=record,
        arrays={"a3_fibula_places_lps": points.copy()},
        physical=points,
        slice_index=0,
    )
    return own, found


def fibula_places(slices: int) -> np.ndarray:
    """One native section's places: a point at (30, 30) on each of the first `slices` slices' planes."""
    return np.asarray([[30.0, 30.0, THICKNESS * z] for z in range(slices)])


def scout(target: Any, leg: run.Leg, source: tuple[Any, Any]) -> Any:
    mapping = run.MapContext(StudyMap(knee="R"), None, None)
    run.fibula_key_planes([target], mapping, [source], leg, STUDY)
    return source[1].record["fibula_key_planes"][target.record["series_uid"]]


def bones(target: Any, leg: run.Leg) -> dict[str, dict]:
    return run.axial_bone_planes(StudyMap(knee="R"), cast(run.Measured, target), leg)


def tally(led: Any, name: str) -> int:
    return sum(1 for event in led.events() if event.name == name)


# The early leg seeds the femur on slices 0 and 2 and holds the tibia far below; the refined leg is that
# leg with one more native tibia place, on slice 1, so the tibia reaches up to the middle of the stack.
FEMUR = [[30.0, 30.0, 0.0], [30.0, 30.0, 6.0]]
EARLY = make_leg(FEMUR, [[5.0, 5.0, -100.0]])
REFINED = make_leg(FEMUR, [[5.0, 5.0, -100.0], [30.0, 30.0, 3.0]])
EQUAL = make_leg(FEMUR, [[5.0, 5.0, -100.0], [30.0, 30.0, 3.0]])


def test_the_axial_bone_planes_decide_on_the_leg_they_are_handed():
    early_target, refined_target = axial_target("early"), axial_target("refined")
    early = bones(early_target, EARLY)
    refined = bones(refined_target, REFINED)

    # the early leg holds the tibia below every slice, so the femur is attributed on both slices it seeds
    assert early["femur"]["statuses"] == {SECTION: 2}
    assert early["femur"]["key_slices"] == [0, 2]
    assert early["tibia"]["statuses"] == {} and early["tibia"]["key_slices"] == []
    # the refined tibia reaches slice 1: the femur's slice 0 now lies within the tibia's native extent
    # and is named, not attributed; its slice 2 stays above it
    assert refined["femur"]["statuses"] == {run.AXIAL_OVERLAP: 1, SECTION: 1}
    assert refined["femur"]["key_slices"] == [2]
    assert refined["tibia"]["statuses"] == {run.AXIAL_OVERLAP: 1}
    assert refined["tibia"]["key_slices"] == []
    assert refined_target.arrays["a4_axial_femur_identity_excluded"].tolist() == [
        True,
        False,
        False,
    ]
    assert early_target.arrays["a4_axial_femur_identity_excluded"].tolist() == [
        False,
        False,
        False,
    ]


def test_a_refined_leg_gets_its_own_projection_and_an_equal_leg_reuses_it():
    target = axial_target("axial")
    with run.recording() as led, run.computing():
        bones(target, EARLY)
        assert tally(led, "leg_on_slice.made") == SLICES
        assert tally(led, "leg_on_slice.handed_on") == 0
        bones(target, REFINED)
        # another identity: every slice's projection is made again, never the early leg's handed on
        assert tally(led, "leg_on_slice.made") == 2 * SLICES
        assert tally(led, "leg_on_slice.handed_on") == 0
        bones(target, EQUAL)
        # a separate leg holding the same places: its identity is the refined leg's, so it reuses
        assert tally(led, "leg_on_slice.made") == 2 * SLICES
        assert tally(led, "leg_on_slice.handed_on") == SLICES
        # the readings of the frame alone are made for the slices some leg seeded (0 and 2) and handed on
        # to every other leg that reads them
        assert tally(led, "coarse_axial_blocks.made") == 2
        assert tally(led, "coarse_axial_depth.made") == 2
        assert tally(led, "coarse_axial_blocks.handed_on") == 2
        assert tally(led, "coarse_axial_depth.handed_on") == 2


def test_the_map_hands_its_leg_to_every_axial_series(monkeypatch):
    seen: list[tuple[Any, Any]] = []
    monkeypatch.setattr(
        run,
        "axial_bone_planes",
        lambda smap, own, leg: seen.append((own, leg)) or {},
    )
    first, second = axial_target("first"), axial_target("second")
    run.build_study_map([first, second], REFINED, (None, None, set()))
    assert len(seen) == 2 and seen[0][0] is first and seen[1][0] is second
    assert all(leg is REFINED for _, leg in seen)


def test_the_fibula_scout_refuses_what_the_refined_tibia_shares():
    source = native_source(fibula_places(2))
    # the tibia of the early leg lies elsewhere on both slices; the refined leg adds a native tibia place
    # inside the fibula's section on slice 0 (the same body, which the coarse section must not attribute)
    elsewhere = [[5.0, 5.0, 0.0], [5.0, 5.0, THICKNESS]]
    early = make_leg([], elsewhere)
    refined = make_leg([], [*elsewhere, [30.0, 33.0, 0.0]])
    with run.computing():
        first = scout(axial_target("early"), early, source)
    source = native_source(fibula_places(2))
    with run.computing():
        second = scout(axial_target("refined"), refined, source)
    assert first["statuses"] == {SECTION: 2} and first["key_slices"] == [0, 1]
    assert second["statuses"] == {SHARED: 1, SECTION: 1}
    assert second["key_slices"] == [1]


def test_the_fibula_scout_keeps_each_legs_projection_apart_and_shares_the_frame_readings():
    target = axial_target("axial")
    elsewhere = [[5.0, 5.0, 0.0], [5.0, 5.0, THICKNESS]]
    early = make_leg([], elsewhere)
    refined = make_leg([], [*elsewhere, [30.0, 33.0, 0.0]])
    equal = make_leg([], [*elsewhere, [30.0, 33.0, 0.0]])
    with run.recording() as led, run.computing():
        scout(target, early, native_source(fibula_places(2)))
        assert tally(led, "leg_on_slice.made") == 2
        scout(target, refined, native_source(fibula_places(2)))
        assert tally(led, "leg_on_slice.made") == 4
        assert tally(led, "leg_on_slice.handed_on") == 0
        scout(target, equal, native_source(fibula_places(2)))
        assert tally(led, "leg_on_slice.made") == 4
        assert tally(led, "leg_on_slice.handed_on") == 2
        # the coarse readings of the two slices belong to the frame: made once, handed to every later leg
        assert tally(led, "coarse_axial_blocks.made") == 2
        assert tally(led, "coarse_axial_blocks.handed_on") == 4
        assert tally(led, "coarse_axial_depth.made") == 2
        assert tally(led, "coarse_axial_depth.handed_on") == 4


def test_the_two_consumers_share_one_projection_of_the_same_refined_leg(monkeypatch):
    asked: list[tuple[str, int, tuple, float, tuple]] = []
    real = run.leg_on

    def spied(leg, series, z, frame, shape, thickness):
        asked.append(
            (
                series.row.series_uid,
                z,
                tuple(shape),
                float(thickness),
                tuple(frame.origin_lps),
            )
        )
        return real(leg, series, z, frame, shape, thickness)

    monkeypatch.setattr(run, "leg_on", spied)
    target = axial_target("axial")
    with run.recording() as led, run.computing():
        bones(target, REFINED)
        bones_asked, made_for_bones = len(asked), tally(led, "leg_on_slice.made")
        scout(target, REFINED, native_source(fibula_places(2)))
        assert tally(led, "leg_on_slice.made") == made_for_bones == SLICES
        assert tally(led, "leg_on_slice.handed_on") == 2
    # the same slice is asked for with the same frame, picture shape and thickness by both consumers,
    # which is what makes the one entry the right answer for each
    by_bones, by_fibula = asked[:bones_asked], asked[bones_asked:]
    assert [row[1] for row in by_fibula] == [0, 1]
    for row in by_fibula:
        assert row in by_bones


# -- the real driver: which leg each reader is handed --------------------------------------------------

FRAME = make_frame((0.0, 0.0, 0.0), [[0.0, 1.0], [1.0, 0.0], [0.0, 0.0]])


@dataclass(frozen=True)
class Series:
    row: SimpleNamespace
    volume: object = None
    slices: tuple = (None,)
    geometry: object = None
    slice_thickness_mm: tuple = ()


def driven(monkeypatch, tmp_path: Path) -> tuple[run.Leg, run.Leg, dict[str, list]]:
    """`measure_study` through its real wiring, the heavy stages stood in for by recorders of the leg each
    one is handed. `refine_leg` returns a leg that is not the early one, so the two can be told apart.
    Returns the early leg, the refined leg and, by reader, the legs that reader was handed."""
    early = make_leg([[0.0, 0.0, 0.0]], [[0.0, 0.0, -50.0]])
    refined = make_leg([[0.0, 0.0, 0.0], [1.0, 1.0, 1.0]], [[0.0, 0.0, -50.0]])
    seen: dict[str, list] = {
        name: []
        for name in (
            "refine",
            "back",
            "semimembranosus",
            "bones",
            "patella",
            "joint",
            "recess",
            "posterior",
            "retinacula",
            "map",
            "fibula",
            "fat",
            "cartilage",
        )
    }
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
        # the leg does not run in this series' plane, so the driver builds the early leg for the readers
        # before the bones, as it does for a study with an axial series
        assignment=SimpleNamespace(in_plane=(False, True, False)),
        stack=None,
    )
    monkeypatch.setattr(
        run,
        "read_study",
        lambda corpus, uid: SimpleNamespace(series=[sag.series]),
    )
    monkeypatch.setattr(run, "measure", lambda series, drawn: sag)
    for name in (
        "name_the_extensor_tendons",
        "name_the_rest_of_the_field",
        "name_joint_boundaries",
        "name_suprapatellar_pads",
        "name_iliotibial_band",
        "name_sartorius",
    ):
        monkeypatch.setattr(run, name, lambda *args: None)

    def recorder(name: str, index: int, result: Any = None):
        def stub(*args):
            seen[name].append(args[index])
            return result

        return stub

    def delegating(name: str, index: int, original):
        def stub(*args):
            seen[name].append(args[index])
            return original(*args)

        return stub

    monkeypatch.setattr(run, "leg_of", lambda measured: early)
    monkeypatch.setattr(
        run,
        "refine_leg",
        lambda carried, measured: (seen["refine"].append(carried), refined)[1],
    )
    monkeypatch.setattr(
        run,
        "name_the_back_of_the_knee",
        lambda own, leg: (seen["back"].append(leg), {})[1],
    )
    monkeypatch.setattr(
        run, "semimembranosus_slice", recorder("semimembranosus", 1, "abstain_x")
    )
    monkeypatch.setattr(run, "gracilis_source", lambda measured, found: "abstain_x")
    monkeypatch.setattr(run, "name_the_bones", recorder("bones", 2))
    monkeypatch.setattr(run, "name_the_patella", recorder("patella", 2))
    monkeypatch.setattr(run, "name_the_joint", recorder("joint", 2))
    monkeypatch.setattr(
        run,
        "name_the_recess",
        lambda measured, partners, leg, *rest: (
            seen["recess"].append(leg),
            [([], []) for _ in measured],
        )[1],
    )
    monkeypatch.setattr(run, "index_posterior", recorder("posterior", 4))
    monkeypatch.setattr(
        run, "retinacula_slice", recorder("retinacula", 1, "abstain_ret")
    )
    monkeypatch.setattr(run, "plane_frame", lambda series, z: FRAME)
    monkeypatch.setattr(run, "find_fibula", lambda *args: "abstain_no_fibula")
    monkeypatch.setattr(run, "acl_slice", lambda *args: "abstain_acl")
    monkeypatch.setattr(run, "lcl_slice", lambda own, fibula_lps: "abstain_lcl")
    monkeypatch.setattr(run, "biceps_femoris_slice", lambda *args: "abstain_biceps")
    for name, key, index in (
        ("build_study_map", "map", 1),
        ("fibula_key_planes", "fibula", 3),
        ("native_fat_pad_candidates", "fat", 3),
        ("name_femoral_cartilage", "cartilage", 4),
    ):
        monkeypatch.setattr(run, name, delegating(key, index, getattr(run, name)))
    run.measure_study(
        cast(run.Corpus, None), "study", tmp_path / "run", tmp_path / "main", False
    )
    return early, refined, seen


def test_the_driver_hands_the_refined_leg_to_the_four_readers_that_follow_it(
    monkeypatch, tmp_path
):
    early, refined, seen = driven(monkeypatch, tmp_path)
    assert early is not refined and early.identity != refined.identity
    # `refine_leg` is given the early leg the bones were named from
    assert len(seen["refine"]) == 1 and seen["refine"][0] is early
    # the bones' own axial key planes (the map) and the fibula's, and the native fat and cartilage contexts
    for name in ("map", "fibula", "fat", "cartilage"):
        assert len(seen[name]) >= 1, name
        assert all(leg is refined for leg in seen[name]), name


def test_the_readers_before_the_bones_and_every_other_reader_keep_the_early_leg(
    monkeypatch, tmp_path
):
    early, _, seen = driven(monkeypatch, tmp_path)
    for name in (
        "back",
        "semimembranosus",
        "bones",
        "patella",
        "joint",
        "recess",
        "posterior",
        "retinacula",
    ):
        assert len(seen[name]) >= 1, name
        assert all(leg is early for leg in seen[name]), name
