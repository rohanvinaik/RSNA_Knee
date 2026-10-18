from __future__ import annotations

from types import SimpleNamespace
from typing import cast

import numpy as np

from knee.collapse import relative as rel
from knee.collapse.observations import Observation, Unresolved
from knee.collapse.physical import PlaneFrame
from knee.collapse.study_map import StudyMap
from scripts import run_interiors as run

FRAME = PlaneFrame(
    np.zeros(3), np.array([[1.0, 0.0], [0.0, 1.0], [0.0, 0.0]]), (1.0, 1.0)
)


def test_completed_family_is_visible_and_partial_or_refused_rows_are_not_promoted(
    monkeypatch,
):
    monkeypatch.setattr(run, "plane_frame", lambda _series, _z: FRAME)
    actual_refine_map = run.refine_map
    refine_calls = []

    def counted_refine_map(*args, **kwargs):
        refine_calls.append(None)
        return actual_refine_map(*args, **kwargs)

    monkeypatch.setattr(run, "refine_map", counted_refine_map)
    series = SimpleNamespace(
        row=SimpleNamespace(series_uid="axial"), slice_thickness_mm=[1.0, 1.0]
    )
    own = SimpleNamespace(
        series=series,
        record={"view": ["Axial", "1", "1"], "observations": []},
    )
    context = run.MapContext(StudyMap(knee="R"), None, None)
    resolved = Observation(
        "patella",
        "native",
        "resolved",
        "axial",
        ("Axial", "1", "1"),
        (1,),
        "identified",
        8,
        0.0,
        "native_support",
        "a native resolved section",
    )
    partial = Observation(
        "joint_fluid",
        "native",
        "reading",
        "axial",
        ("Axial", "1", "1"),
        (1,),
        "partial_reading",
        None,
        0.0,
        "partial_support",
        "a reading, not resolved support",
    )
    laid = Observation(
        "patella",
        "laid",
        "resolved",
        "axial",
        ("Axial", "1", "1"),
        (1,),
        "laid_from_partner",
        12,
        0.0,
        "laid_support",
        "laid evidence is not a native map offer",
    )
    unknown = Observation(
        "not_an_object",
        "native",
        "resolved",
        "axial",
        ("Axial", "1", "1"),
        (1,),
        "identified",
        18,
        0.0,
        "unknown_support",
        "an unknown name is not map evidence",
    )
    refusal = Unresolved(
        "joint_capsule", "native", "axial", ("Axial", "1", "1"), "not_read"
    )
    said = [([resolved, partial, laid, unknown], [refusal])]

    product, map_rows, added = run.offer_native_family(
        context, [cast(run.Measured, own)], "test_family", said
    )
    assert product == "test_family.map_rows" and len(map_rows) == 1 and added == 1
    selected = context.smap.selected("patella", "axial")
    assert selected.outcome == "selected" and selected.slice == 1
    assert context.smap.selected("joint_fluid", "axial").outcome == "not_supplied"
    assert context.smap.selected("joint_capsule", "axial").outcome == "not_supplied"
    assert context.smap.selected("not_an_object", "axial").outcome == "not_supplied"
    version = context.smap.version
    _, duplicate_rows, duplicate_added = run.offer_native_family(
        context, [cast(run.Measured, own)], "test_family", said
    )
    assert duplicate_rows and duplicate_added == 0
    assert context.smap.version == version
    assert len(context.smap.candidates[("patella", "axial")]) == 1
    assert len(refine_calls) == 2
    empty_product, empty_rows, empty_added = run.offer_native_family(
        context,
        [cast(run.Measured, own)],
        "empty_family",
        [([], [refusal])],
    )
    assert (empty_product, empty_rows, empty_added) == ("empty_family.map_rows", [], 0)
    assert len(refine_calls) == 2


def test_later_guide_reads_the_map_after_native_evidence_is_offered(monkeypatch):
    axial_frames = [
        PlaneFrame.from_dicom((0.0, 0.0, float(z)), (1, 0, 0, 0, 1, 0), (1.0, 1.0))
        for z in range(3)
    ]
    monkeypatch.setattr(run, "plane_frame", lambda _series, z: axial_frames[z])
    smap = StudyMap(knee="R")
    for orientation, origin, direction in (
        ("sagittal", (5.0, 0.0, 0.0), (0, 1, 0, 0, 0, -1)),
        ("coronal", (0.0, 6.0, 0.0), (1, 0, 0, 0, 0, -1)),
    ):
        frame = PlaneFrame.from_dicom(origin, direction, (1.0, 1.0))
        smap.offer(
            "patella",
            rel.plane_of_frame(
                "patella",
                orientation,
                series_uid=f"seed-{orientation}",
                slice=0,
                frame=frame,
                precision_mm=0.5,
            ),
            20.0,
            "seed",
        )
    own = SimpleNamespace(
        series=SimpleNamespace(
            row=SimpleNamespace(series_uid="axial"),
            volume=np.zeros((3, 10, 10)),
            slice_thickness_mm=[1.0, 1.0, 1.0],
        ),
        arrays={"acquired_plane": np.zeros((10, 10))},
        record={"view": ["Axial", "1", "1"], "observations": []},
    )

    def ideal(origin, target, knee_scale_mm=None):
        if origin == "patella" and target == "joint_fluid":
            return rel.IdealVector(origin, target, (0.0, 0.0, 0.0), "fixture")
        return None

    context = run.MapContext(smap, ideal, None)
    cold = context.guide("joint_fluid", cast(run.Measured, own))
    assert cold.status.startswith("unguided:")
    before = smap.version
    native = Observation(
        "patella",
        "native",
        "resolved",
        "axial",
        ("Axial", "1", "1"),
        (1,),
        "identified",
        8,
        0.0,
        "native_support",
        "native axial support",
    )
    product, map_rows, added = run.offer_native_family(
        context,
        [cast(run.Measured, own)],
        "patella_native",
        [([native], [])],
    )
    assert product == "patella_native.map_rows" and map_rows and added == 1
    after = smap.version
    warm = context.guide("joint_fluid", cast(run.Measured, own))
    assert after > before
    assert warm.status == "guided"
    assert warm.anchors == ("patella",)
    assert warm.placements[0]["anchor"] == "patella"
    assert warm.placements[0]["point_lps"] == [5.0, 6.0, 1.0]
