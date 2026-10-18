from types import SimpleNamespace
from typing import cast

import numpy as np

from knee.collapse import relative as rel
from knee.collapse.physical import PlaneFrame
from knee.collapse.profile import FineReading
from knee.collapse.study_map import StudyMap
from scripts import run_interiors as run

SAG = (0, 1, 0, 0, 0, -1)
COR = (1, 0, 0, 0, 0, -1)
AXI = (1, 0, 0, 0, 1, 0)


def frame(orientation, origin):
    return PlaneFrame.from_dicom(origin, orientation, (1.0, 1.0))


def positioned_map(monkeypatch):
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
        for orientation, f in planes:
            smap.offer(
                name,
                rel.plane_of_frame(
                    name,
                    orientation,
                    series_uid=f"{name}-{orientation}",
                    slice=0,
                    frame=f,
                    precision_mm=1.0,
                ),
                100.0,
                "test anatomy",
            )

    # Both complete anchors predict the same sagittal slice, at different in-plane places.
    def ideal(origin, target, _scale):
        vectors = {
            ("femur", "medial_meniscus"): (0.0, 0.0, 0.0),
            ("tibia", "medial_meniscus"): (2.0, -10.0, 35.0),
        }
        vector = vectors.get((origin, target))
        return (
            None
            if vector is None
            else rel.IdealVector(origin, target, vector, "test anatomy")
        )

    origins = [-20.0, -18.0, -16.0, -14.0, -12.0, -10.0, -8.0, -6.0]
    frames = [frame(SAG, (x, -100.0, 100.0)) for x in origins]
    monkeypatch.setattr(run, "plane_frame", lambda _series, z: frames[z])
    series = SimpleNamespace(
        row=SimpleNamespace(series_uid="sag"),
        volume=np.zeros((len(frames), 200, 200)),
    )
    own = cast(
        run.Measured,
        SimpleNamespace(
            series=series,
            record={"slice_index": 4},
            arrays={"acquired_plane": np.zeros((200, 200))},
        ),
    )
    context = run.MapContext(smap, ideal, lambda _name, _scale: (0.0, 0.0, 0.0))
    return context, own


def profile_with_fine_support(guide, hit_anchor):
    placements = [row for row in guide.placements if row["status"] == "ok"]
    readings = []
    for index in sorted({int(row["slice"]) for row in placements}):
        center = next(row["rc"] for row in placements if row["anchor"] == hit_anchor)
        if (
            int(next(row["slice"] for row in placements if row["anchor"] == hit_anchor))
            != index
        ):
            center = next(row["rc"] for row in placements if int(row["slice"]) == index)
            active = False
        else:
            active = True
        body = np.zeros((100, 100), dtype=bool)
        if active:
            r, c = (round(value / 2.0) for value in center)
            body[r, c] = True
        readings.append(
            FineReading(
                index,
                (0, 200, 0, 200),
                (2, 2),
                (2.0, 2.0),
                np.full((100, 100), 2.0),
                body,
                body,
            )
        )
    depth = len(guide.slices) + 8
    return run.JointProfile(
        names=(run.DARK,),
        status={run.DARK: np.zeros(depth, dtype=np.int8)},
        area_mm2={run.DARK: np.zeros(depth)},
        seen_blocks=np.zeros(depth, dtype=np.int32),
        unseen_blocks=np.zeros(depth, dtype=np.int32),
        corridor_px=np.zeros(depth, dtype=np.int32),
        corridor=np.zeros((depth, 1, 1), dtype=bool),
        could={run.DARK: np.zeros((depth, 1, 1), dtype=bool)},
        window_rc=np.full((depth, 4), -1, dtype=np.int32),
        cell_mm=np.full((depth, 2), np.nan),
        block_px=np.full((depth, 2), -1, dtype=np.int32),
        fine=tuple(readings),
        level={run.DARK: (1.0, 3.0)},
    )


def test_real_study_map_guides_union_all_anchor_placements_and_question_window(
    monkeypatch,
):
    mapping, own = positioned_map(monkeypatch)
    window, detail = run.joint_map_neighbourhood(
        own, mapping, {"body:medial_meniscus": run.DARK}
    )
    target = detail["map_questions"]["body:medial_meniscus"]["targets"][0]
    assert window is not None
    assert np.flatnonzero(window).tolist() == [4, 5]
    assert target["status"] == "guided"
    assert target["anchors"] == ["femur", "tibia"]
    assert [row["status"] for row in target["placements"]] == ["ok", "ok"]
    assert [row["slice"] for row in target["placements"]] == [5, 5]
    assert target["placements"][0]["rc"] != target["placements"][1]["rc"]


def test_real_map_guide_places_native_fine_support_and_orders_guided_question_run(
    monkeypatch,
):
    mapping, own = positioned_map(monkeypatch)
    _, detail = run.joint_map_neighbourhood(
        own, mapping, {"body:medial_meniscus": run.DARK}
    )
    guide = mapping.guide("medial_meniscus", own)
    profile = profile_with_fine_support(guide, "tibia")
    asks = {"body:medial_meniscus": run.DARK}
    hits = run.joint_guide_spatial_hits(profile, asks, detail)
    assert hits["body:medial_meniscus"] == {5: True}

    rows = [(9.0, run.DARK, [7]), (4.0, run.DARK, [5])]
    assert run.order_joint_runs(rows, asks, hits) == [rows[1], rows[0]]
    assert run.order_joint_runs(rows, asks, {}) == rows


def test_question_without_complete_map_guide_requires_full_depth(monkeypatch):
    mapping, own = positioned_map(monkeypatch)
    mapping.smap = StudyMap(knee="R")
    window, detail = run.joint_map_neighbourhood(own, mapping, {"mcl": run.DARK})
    assert window is None
    assert detail["code"] == "full_depth_required_for_unguided_questions"
    assert detail["unguided_questions"]["mcl"] == [
        "unguided:no_complete_anchor_with_an_ideal"
    ]


def test_noncontiguous_equal_support_rows_are_consumed_as_one_tie_group():
    asks = {
        "body:medial_meniscus": run.DARK,
        "body:lateral_meniscus": run.DARK,
    }
    rows = [
        (8.0, run.DARK, [2]),
        (7.0, run.LIGAMENT, [3]),
        (8.0, run.DARK, [5]),
    ]
    hits = {
        "body:medial_meniscus": {2: False, 5: True},
        "body:lateral_meniscus": {},
    }
    ordered = run.order_joint_runs(rows, asks, hits)
    groups = run.joint_run_groups(ordered)
    consumed = [row for group in groups for row in group]
    assert len(consumed) == len(rows)
    assert sorted(row[2][0] for row in consumed) == [2, 3, 5]
    assert [row[2][0] for row in groups[0]] == [5, 2]
    assert groups[1] == [rows[1]]


def test_spatial_guidance_projects_onto_every_read_slice_in_the_expected_allowance(
    monkeypatch,
):
    from dataclasses import replace

    mapping, own = positioned_map(monkeypatch)
    mapping.span = lambda _name, _scale: (4.0, 0.0, 0.0)
    asks = {"body:medial_meniscus": run.DARK}
    _, detail = run.joint_map_neighbourhood(own, mapping, asks)
    guide = mapping.guide("medial_meniscus", own)
    profile = profile_with_fine_support(guide, "tibia")
    first = profile.fine[0]
    # The physical target's nearest plane is 5. The candidate is on another permitted plane,
    # with its own geometry; it must not force an unnecessary full-depth fallback.
    profile = replace(profile, fine=(replace(first, index=6),))
    hits = run.joint_guide_spatial_hits(profile, asks, detail, own=own)
    assert hits["body:medial_meniscus"][6] is True

    # A native slice outside the map allowance must not acquire a hit by projection.
    profile = replace(profile, fine=(replace(first, index=0),))
    hits = run.joint_guide_spatial_hits(profile, asks, detail, own=own)
    assert 0 not in hits["body:medial_meniscus"]
