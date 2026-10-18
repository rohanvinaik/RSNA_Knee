"""Cross-view patella scouting preserves native addresses and remains a coarse reading."""

from __future__ import annotations

from types import SimpleNamespace
from typing import cast

import numpy as np

from knee.collapse import relative as rel
from knee.collapse.physical import PlaneFrame
from knee.collapse.study_map import StudyMap
from scripts import run_interiors as run

PROOF = "1.2.826.0.1.3680043.8.498.10095687747295410396510538520594649149"


def frame(origin: tuple[float, float, float], basis: list[list[float]]) -> PlaneFrame:
    return PlaneFrame(np.asarray(origin), np.asarray(basis, dtype=float), (1.0, 1.0))


def enclosed() -> np.ndarray:
    rr, cc = np.mgrid[:64, :64]
    radius = np.hypot(rr - 30, cc - 30)
    image = np.full((64, 64), 100.0)
    image[radius <= 8] = 30.0
    image[(radius > 8) & (radius <= 10)] = 5.0
    image[(radius > 10) & (radius <= 12)] = 200.0
    return image


def test_native_sagittal_mask_projects_as_location_seed_and_scout_is_reading(
    monkeypatch,
):
    sagittal = frame((30.0, 0.0, 50.0), [[0, 0], [1, 0], [0, -1]])
    coronal = frame((0.0, 30.0, 50.0), [[1, 0], [0, 0], [0, -1]])
    axial = frame((0.0, 0.0, 26.0), [[1, 0], [0, 1], [0, 0]])
    frames = {"sagittal": sagittal, "coronal": coronal, "axial": axial}
    monkeypatch.setattr(
        run,
        "plane_frame",
        lambda series, z: frames[str(series.view).lower()],
    )
    monkeypatch.setattr(
        run,
        "artifact_of",
        lambda study_uid, record: f"{study_uid}:{record['series_uid']}",
    )
    monkeypatch.setattr(
        run,
        "map_plane",
        lambda own, obj, z, reason, provenance: rel.plane_of_frame(
            obj,
            str(own.series.view).lower(),
            series_uid=own.record["series_uid"],
            slice=z,
            frame=frames[str(own.series.view).lower()],
            precision_mm=1.0,
        ),
    )

    source_mask = np.zeros((64, 64), dtype=np.int32)
    source_mask[18:43, 18:43] = 7
    source_series = SimpleNamespace(
        view="sagittal",
        row=SimpleNamespace(series_uid="source", fat_suppression="1"),
        slice_thickness_mm=[3.0],
    )
    source = SimpleNamespace(
        series=source_series,
        record={
            "series_uid": "source",
            "view": ["Sagittal", "1", "1"],
            "observations": [
                {
                    "object": "patella",
                    "provenance": "native",
                    "kind": "resolved",
                    "code": "identified",
                    "support": "a1_objects",
                    "label": 7,
                    "slices": [0],
                }
            ],
        },
        arrays={"a1_objects": source_mask},
    )
    targets = []
    for orientation in ("coronal", "axial"):
        series = SimpleNamespace(
            view=orientation,
            row=SimpleNamespace(
                series_uid=orientation,
                fat_suppression="1",
            ),
            volume=np.asarray([enclosed()]),
            slice_thickness_mm=[3.0],
        )
        targets.append(
            SimpleNamespace(
                series=series,
                record={
                    "series_uid": orientation,
                    "view": [orientation.title(), "1", "1"],
                    "observations": [],
                },
                arrays={},
            )
        )
    measured = cast(list[run.Measured], [source, *targets])
    mapping = run.MapContext(StudyMap(knee="R"), None, None)

    with run.computing():
        run.patella_key_planes(measured, mapping, PROOF)

    for own in targets:
        assert own.record["patella_key_planes"]["key_slices"] == [0]
        assert own.record["patella_key_planes"]["source_sections"] == 1
        assert own.arrays["a4_patella_coarse_source_extent"].tolist() == [True]
        assert own.arrays["a4_patella_coarse_origin_lps"].shape == (1, 3)
        assert own.arrays["a4_patella_coarse_normal_lps"].shape == (1, 3)
        assert own.arrays["a4_patella_coarse_thickness_mm"].tolist() == [3.0]
        assert own.arrays["a4_patella_coarse_patella_body"].any()
        reading = next(
            row
            for row in own.record["observations"]
            if row["object"] == "patella" and row["kind"] == "reading"
        )
        assert reading["support"] == "a4_patella_coarse_patella_body"
        assert reading["artifact"] == f"{PROOF}:{own.record['series_uid']}"
        assert not any(
            row["kind"] == "resolved" and row["support"].startswith("a4_")
            for row in own.record["observations"]
        )
        selected = mapping.smap.selected("patella", str(own.series.view).lower())
        assert selected.outcome == rel.SELECTED
        assert selected.series_uid == own.record["series_uid"]
