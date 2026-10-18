from types import SimpleNamespace
from typing import cast

import numpy as np

from knee.collapse import relative as rel
from knee.collapse.physical import PlaneFrame
from knee.collapse.profile import FineReading
from knee.collapse.study_map import Guide, StudyMap
from scripts import run_interiors as run

SAG = (0, 1, 0, 0, 0, -1)
COR = (1, 0, 0, 0, 0, -1)
AXI = (1, 0, 0, 0, 1, 0)


def frame(orientation, origin):
    return PlaneFrame.from_dicom(origin, orientation, (1.0, 1.0))


def recess_profile(depth, support=None):
    support = {} if support is None else support
    area = np.zeros(depth)
    for z, value in support.items():
        area[z] = value
    return run.JointProfile(
        names=(run.FLUID,),
        status={run.FLUID: np.full(depth, run.JOINT_BODY, dtype=np.int8)},
        area_mm2={run.FLUID: area},
        seen_blocks=np.zeros(depth, dtype=np.int32),
        unseen_blocks=np.zeros(depth, dtype=np.int32),
        corridor_px=np.zeros(depth, dtype=np.int32),
        corridor=np.zeros((depth, 1, 1), dtype=bool),
        could={run.FLUID: np.zeros((depth, 1, 1), dtype=bool)},
        window_rc=np.full((depth, 4), -1, dtype=np.int32),
        cell_mm=np.full((depth, 2), np.nan),
        block_px=np.full((depth, 2), -1, dtype=np.int32),
        fine=(),
        level={run.FLUID: (0.5, 5.5)},
    )


def mapped_recess(monkeypatch):
    femur = (-10.0, -20.0, 30.0)
    tibia = (-12.0, -18.0, -5.0)
    smap = StudyMap(knee="R")
    for name, point in (("femur", femur), ("tibia", tibia)):
        x, y, z = point
        planes = (
            ("sagittal", frame(SAG, (x, -100.0, 100.0))),
            ("coronal", frame(COR, (0.0, y, 100.0))),
            ("axial", frame(AXI, (0.0, 0.0, z))),
        )
        for orientation, place in planes:
            smap.offer(
                name,
                rel.plane_of_frame(
                    name,
                    orientation,
                    series_uid=f"{name}-{orientation}",
                    slice=0,
                    frame=place,
                    precision_mm=1.0,
                ),
                100.0,
                "anatomical test reference",
            )

    def ideal(origin, target, _scale):
        vector = {
            "femur": (0.0, 0.0, 0.0),
            "tibia": (2.0, -10.0, 35.0),
        }.get(origin)
        return (
            None
            if vector is None
            else rel.IdealVector(origin, target, vector, "anatomical test reference")
        )

    origins = [-20.0, -18.0, -16.0, -14.0, -12.0, -10.0, -8.0, -6.0]
    frames = [frame(SAG, (x, -100.0, 100.0)) for x in origins]
    monkeypatch.setattr(run, "plane_frame", lambda _series, z: frames[z])
    own = cast(
        run.Measured,
        SimpleNamespace(
            series=SimpleNamespace(
                row=SimpleNamespace(series_uid="sag"),
                volume=np.zeros((len(frames), 200, 200)),
            ),
            record={"slice_index": 4},
            arrays={"acquired_plane": np.zeros((200, 200))},
        ),
    )
    mapping = run.MapContext(smap, ideal, lambda _name, _scale: (0.0, 0.0, 0.0))
    return mapping, own


def test_recess_map_uses_all_anatomical_targets_and_keeps_anchor_placements(
    monkeypatch,
):
    mapping, own = mapped_recess(monkeypatch)

    window, detail = run.recess_map_neighbourhood(own, mapping, "anterior")

    assert window is not None
    assert np.flatnonzero(window).tolist() == [4, 5]
    assert detail["code"] == "anatomical_map_guides"
    assert [entry["object"] for entry in detail["targets"]] == [
        "anterior_synovial_recess",
        "synovium",
        "joint_fluid",
    ]
    assert all(entry["status"] == "guided" for entry in detail["targets"])
    assert all(entry["anchors"] == ["femur", "tibia"] for entry in detail["targets"])
    assert all(len(entry["placements"]) == 2 for entry in detail["targets"])


def test_one_unusable_recess_guide_broadens_to_the_full_profile():
    class MissingOne:
        def guide(self, name, _own):
            if name == "synovium":
                return Guide(name, "sag", "unguided:no_complete_anchor")
            return Guide(
                name,
                "sag",
                "guided",
                slices=(5,),
                rcs=((5, (10.0, 10.0)),),
                placements=(
                    {
                        "anchor": "femur",
                        "status": "ok",
                        "slice": 5,
                        "rc": [10.0, 10.0],
                    },
                ),
                half_px=(0.0, 0.0),
            )

    own = cast(
        run.Measured,
        SimpleNamespace(
            series=SimpleNamespace(volume=np.zeros((8, 20, 20))),
            record={"slice_index": 3},
        ),
    )

    window, detail = run.recess_map_neighbourhood(
        own, cast(run.MapContext, MissingOne()), "anterior"
    )

    assert window is None
    assert detail["code"] == "full_depth_required_for_unusable_anatomical_guide"
    assert detail["unguided_targets"] == {"synovium": "unguided:no_complete_anchor"}


def test_spatial_hit_promotes_every_tied_best_slice_of_the_supported_run(monkeypatch):
    mapping, own = mapped_recess(monkeypatch)
    _window, detail = run.recess_map_neighbourhood(own, mapping, "anterior")
    first = detail["targets"][0]
    placement = next(p for p in first["placements"] if p["status"] == "ok")
    z = int(placement["slice"])
    row, col = (round(value) for value in placement["rc"])
    body = np.zeros((200, 200), dtype=bool)
    body[row, col] = True
    fine = FineReading(
        z,
        (0, 200, 0, 200),
        (1, 1),
        (1.0, 1.0),
        np.ones((200, 200)),
        body,
        body,
    )
    depth = len(own.series.volume)
    area = np.zeros(depth)
    area[z : z + 2] = 1.0
    profile = run.JointProfile(
        names=(run.FLUID,),
        status={run.FLUID: np.full(depth, run.JOINT_BODY, dtype=np.int8)},
        area_mm2={run.FLUID: area},
        seen_blocks=np.zeros(depth, dtype=np.int32),
        unseen_blocks=np.zeros(depth, dtype=np.int32),
        corridor_px=np.zeros(depth, dtype=np.int32),
        corridor=np.zeros((depth, 1, 1), dtype=bool),
        could={run.FLUID: np.zeros((depth, 1, 1), dtype=bool)},
        window_rc=np.full((depth, 4), -1, dtype=np.int32),
        cell_mm=np.full((depth, 2), np.nan),
        block_px=np.full((depth, 2), -1, dtype=np.int32),
        fine=(fine,),
        level={run.FLUID: (0.5, 1.5)},
    )

    points, hits = run.recess_guided_points(profile, detail)

    assert hits["recess"][z] is True
    assert sorted(points) == [z, z + 1]


def test_guided_location_without_fluid_support_does_not_point_a_native_plane(
    monkeypatch,
):
    mapping, own = mapped_recess(monkeypatch)
    _window, detail = run.recess_map_neighbourhood(own, mapping, "anterior")
    depth = len(own.series.volume)
    profile = run.JointProfile(
        names=(run.FLUID,),
        status={run.FLUID: np.full(depth, run.JOINT_NONE, dtype=np.int8)},
        area_mm2={run.FLUID: np.zeros(depth)},
        seen_blocks=np.zeros(depth, dtype=np.int32),
        unseen_blocks=np.zeros(depth, dtype=np.int32),
        corridor_px=np.zeros(depth, dtype=np.int32),
        corridor=np.zeros((depth, 1, 1), dtype=bool),
        could={run.FLUID: np.zeros((depth, 1, 1), dtype=bool)},
        window_rc=np.full((depth, 4), -1, dtype=np.int32),
        cell_mm=np.full((depth, 2), np.nan),
        block_px=np.full((depth, 2), -1, dtype=np.int32),
        fine=(),
        level={run.FLUID: (0.5, 1.5)},
    )

    points, hits = run.recess_guided_points(profile, detail)

    assert points == {}
    assert hits["recess"] == {5: False}


def test_edge_walk_finds_interior_peak_then_fallback_reads_only_unvisited_slices():
    depth = 10
    initial = np.zeros(depth, dtype=bool)
    initial[2:5] = True
    profile = recess_profile(depth, {2: 1.0, 3: 2.0, 4: 3.0})
    read_batches = []

    def profile_on(visit):
        slices = np.flatnonzero(visit).tolist()
        read_batches.append(slices)
        support = {z: {5: 4.0, 6: 5.0, 7: 2.0}.get(z, 0.0) for z in slices}
        return recess_profile(depth, support)

    walked_profile, visited, walked = run.recess_walk_boundary_peaks(
        profile, initial, profile_on
    )
    runs = run.positive_runs(walked_profile.area_mm2[run.FLUID])
    maxima = run.run_maxima(walked_profile.area_mm2[run.FLUID], runs)

    assert read_batches == [[5], [6], [7]]
    assert np.flatnonzero(walked).tolist() == [5, 6, 7]
    assert np.flatnonzero(visited).tolist() == [2, 3, 4, 5, 6, 7]
    assert maxima == [(6,)]

    full_profile, visited, broadened = run.recess_complete_unvisited_profile(
        walked_profile, visited, profile_on
    )

    assert broadened is True
    assert read_batches[-1] == [0, 1, 8, 9]
    assert visited.all()
    assert np.flatnonzero(full_profile.area_mm2[run.FLUID]).tolist() == [
        2,
        3,
        4,
        5,
        6,
        7,
    ]


def test_recess_spatial_hit_projects_anchor_onto_an_allowed_peak_slice(monkeypatch):
    _mapping, own = mapped_recess(monkeypatch)
    point = [-12.0, -20.0, 30.0]
    frame_at_peak = run.plane_frame(own.series, 4)
    assert not isinstance(frame_at_peak, str)
    row, col = frame_at_peak.to_native(np.asarray([point], dtype=float))[0]
    body = np.zeros((200, 200), dtype=bool)
    body[round(row), round(col)] = True
    fine = FineReading(
        4,
        (0, 200, 0, 200),
        (1, 1),
        (1.0, 1.0),
        np.ones((200, 200)),
        body,
        body,
    )
    base = recess_profile(len(own.series.volume), {4: 1.0})
    profile = run.JointProfile(
        base.names,
        base.status,
        base.area_mm2,
        base.seen_blocks,
        base.unseen_blocks,
        base.corridor_px,
        base.corridor,
        base.could,
        base.window_rc,
        base.cell_mm,
        base.block_px,
        (fine,),
        base.level,
    )
    guidance = {
        "targets": [
            {
                "status": "guided",
                "slices": [4, 5],
                "half_px": [0.0, 0.0],
                "placements": [
                    {
                        "status": "ok",
                        "slice": 5,
                        "rc": [0.0, 0.0],
                        "point_lps": point,
                    }
                ],
            }
        ]
    }

    legacy_points, legacy_hits = run.recess_guided_points(profile, guidance)
    projected_points, projected_hits = run.recess_guided_points(
        profile, guidance, own=own
    )

    assert legacy_points == {}
    assert legacy_hits["recess"] == {5: False}
    assert projected_hits["recess"][4] is True
    assert projected_points == {4: ["fluid"]}


def test_nonpeak_support_selects_its_extended_run_and_keeps_true_peak(monkeypatch):
    depth = 10
    profile = recess_profile(depth, {4: 1.0, 5: 2.0, 6: 3.0})
    monkeypatch.setattr(
        run,
        "joint_guide_spatial_hits",
        lambda *_args, **_kwargs: {"recess": {4: True}},
    )

    points, hits = run.recess_guided_points(profile, {"targets": []})

    assert hits["recess"] == {4: True}
    assert points == {6: ["fluid"]}
