from dataclasses import replace
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


def real_fibula_guide(monkeypatch):
    anchors = {"femur": (-10.0, -20.0, 30.0), "tibia": (-12.0, -18.0, -5.0)}
    smap = StudyMap(knee="R")
    for name, point in anchors.items():
        x, y, z = point
        for orientation, plane_frame in (
            ("sagittal", frame(SAG, (x, -100.0, 100.0))),
            ("coronal", frame(COR, (0.0, y, 100.0))),
            ("axial", frame(AXI, (0.0, 0.0, z))),
        ):
            smap.offer(
                name,
                rel.plane_of_frame(
                    name,
                    orientation,
                    series_uid=f"{name}-{orientation}",
                    slice=0,
                    frame=plane_frame,
                    precision_mm=1.0,
                ),
                10.0,
                "test key plane",
            )

    def ideal(origin, target, _scale):
        if target != "fibula":
            return None
        vectors = {
            "femur": (-10.0, -5.0, -10.0),
            "tibia": (-8.0, -7.0, 25.0),
        }
        vector = vectors.get(origin)
        return (
            None
            if vector is None
            else rel.IdealVector(origin, target, vector, "test anatomy")
        )

    frames = [frame(SAG, (-24.0 + 2.0 * z, -100.0, 100.0)) for z in range(8)]
    monkeypatch.setattr(run, "plane_frame", lambda _series, z: frames[z])
    series = SimpleNamespace(
        row=SimpleNamespace(series_uid="sagittal"),
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
    mapping = run.MapContext(smap, ideal, lambda _name, _scale: (8.0, 8.0, 8.0))
    return mapping, own


def profile_at_guide(guide, include_candidate=True):
    readings = []
    expected = next(row for row in guide.placements if row["status"] == "ok")
    for z in guide.slices:
        rc = expected["rc"]
        body = np.zeros((100, 100), dtype=bool)
        if include_candidate:
            row, col = (round(value / 2.0) for value in rc)
            body[row, col] = True
        readings.append(
            FineReading(
                int(z),
                (0, 200, 0, 200),
                (2, 2),
                (2.0, 2.0),
                np.ones((100, 100)),
                body,
                body,
            )
        )
    return run.FibulaProfile(
        status=np.zeros(8, dtype=np.int8),
        area_mm2=np.ones(8),
        centroid_lps=np.full((8, 3), np.nan),
        candidates=np.ones(8, dtype=np.int32),
        corridor=np.zeros((8, 1, 1), dtype=bool),
        could=np.zeros((8, 1, 1), dtype=bool),
        window_rc=np.zeros((8, 4), dtype=np.int32),
        cell_mm=np.ones((8, 2)),
        block_px=np.full((8, 2), 2, dtype=np.int32),
        fine=tuple(readings),
        light=1.0,
        top_mm=0.0,
        middle_lps=np.zeros(3),
    )


def test_real_study_map_checks_expected_slice_and_in_plane_fibula_body(monkeypatch):
    mapping, own = real_fibula_guide(monkeypatch)
    guide = mapping.guide("fibula", own)
    assert guide.status == "guided"
    assert guide.anchors == ("femur", "tibia")
    assert guide.slices == (0, 1, 2, 3, 4)

    profile = profile_at_guide(guide)
    hits = run.fibula_guided_slices(own.series, profile, guide)
    assert hits == {0: True, 1: True, 2: True, 3: True, 4: True}

    groups = run.fibula_detail_groups([1, 2, 4, 6], hits)
    assert groups == [("guided", [1, 2, 4]), ("broadened", [6])]


def test_wrong_in_plane_body_broadens_all_supported_fibula_pointers(monkeypatch):
    mapping, own = real_fibula_guide(monkeypatch)
    guide = mapping.guide("fibula", own)
    profile = profile_at_guide(guide, include_candidate=False)

    hits = run.fibula_guided_slices(own.series, profile, guide)
    assert hits == {0: False, 1: False, 2: False, 3: False, 4: False}
    assert run.fibula_detail_groups([1, 2, 4, 6], hits) == [
        ("full_supported", [1, 2, 4, 6])
    ]


def test_missing_guide_preserves_legacy_full_supported_search():
    assert run.fibula_detail_groups([2, 5], {}) == [("full_supported", [2, 5])]


def test_map_hit_keeps_all_tied_maxima_and_run_cut_confirmation(monkeypatch):
    mapping, own = real_fibula_guide(monkeypatch)
    guide = mapping.guide("fibula", own)
    profile = profile_at_guide(guide)
    hits = run.fibula_guided_slices(own.series, profile, guide)
    sparse_hits = {z: z == 1 for z in hits}

    groups = run.fibula_detail_groups(
        [3, 4, 5, 7],
        sparse_hits,
        runs=[(0, 5), (6, 8)],
        maxima=[np.asarray([3, 4]), np.asarray([7])],
        run_confirmations=[5],
    )
    assert groups == [("guided", [3, 4, 5]), ("broadened", [7])]


def test_broadened_profile_reuses_guided_slices_and_fills_only_the_remainder(
    monkeypatch,
):
    mapping, own = real_fibula_guide(monkeypatch)
    guide = mapping.guide("fibula", own)
    first = profile_at_guide(guide)
    first.status[:5] = 1
    first.area_mm2[:5] = np.arange(1.0, 6.0)
    extra = FineReading(
        5,
        (0, 200, 0, 200),
        (2, 2),
        (2.0, 2.0),
        np.ones((100, 100)),
        np.zeros((100, 100), dtype=bool),
        np.zeros((100, 100), dtype=bool),
    )
    second = replace(
        first,
        status=np.full(8, 2, dtype=np.int8),
        area_mm2=np.full(8, 20.0),
        fine=(extra,),
    )

    merged = run.merge_fibula_profiles(
        first, second, np.array([False, False, False, False, False, True, False, False])
    )
    assert merged.status[:5].tolist() == [1, 1, 1, 1, 1]
    assert merged.status[5:].tolist() == [2, 0, 0]
    assert merged.area_mm2[:6].tolist() == [1.0, 2.0, 3.0, 4.0, 5.0, 20.0]
    assert [reading.index for reading in merged.fine] == [0, 1, 2, 3, 4, 5]
