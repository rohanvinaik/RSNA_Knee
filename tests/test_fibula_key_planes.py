"""The fibula's axial key plane is scouted from native sagittal/coronal sections as a coarse reading.

Native section places are location seeds only; the target series' own 2 mm enclosed section is the
reading, kept beside the observations the holder already carries and offered to the study map.
"""

from __future__ import annotations

import math
from collections.abc import Sequence
from types import SimpleNamespace
from typing import Any, cast

import numpy as np
import pytest

from knee.collapse import relative as rel
from knee.collapse.coarse_section import SECTION, SHARED
from knee.collapse.physical import PlaneFrame
from knee.collapse.study_map import StudyMap
from scripts import run_interiors as run

PROOF = "1.2.826.0.1.3680043.8.498.10095687747295410396510538520594649149"
HOLDER = "holder-sagittal"


def make_frame(origin: Sequence[float], basis: Sequence[Sequence[float]]) -> PlaneFrame:
    return PlaneFrame(np.asarray(origin), np.asarray(basis, dtype=float), (1.0, 1.0))


def axial_frame(z: float) -> PlaneFrame:
    return make_frame((0.0, 0.0, z), [[1, 0], [0, 1], [0, 0]])


SAGITTAL = make_frame((30.0, 0.0, 50.0), [[0, 0], [1, 0], [0, -1]])
CORONAL = make_frame((0.0, 30.0, 50.0), [[1, 0], [0, 0], [0, -1]])


def enclosed(radius: float = 8.0) -> np.ndarray:
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
    """Each stub series carries its own frames; a string is a header that cannot be read."""
    monkeypatch.setattr(run, "plane_frame", lambda series, z: series.frames[z])


def axial_target(
    uid: str,
    radii: list[float],
    frames: list[Any] | None = None,
    thicknesses: list[float | None] | None = None,
    volume: bool = True,
) -> Any:
    count = len(radii)
    series = SimpleNamespace(
        view="axial",
        row=SimpleNamespace(series_uid=uid, fat_suppression="1"),
        volume=np.asarray([enclosed(r) for r in radii]) if volume else None,
        slice_thickness_mm=thicknesses if thicknesses is not None else [3.0] * count,
        frames=frames
        if frames is not None
        else [axial_frame(3.0 * z) for z in range(count)],
    )
    return SimpleNamespace(
        series=series,
        record={"series_uid": uid, "view": ["Axial", "1", "1"], "observations": []},
        arrays={},
    )


def native_source(
    uid: str,
    view: str,
    points: np.ndarray,
    frame: Any = None,
    thickness: float | None = 3.0,
    observations: list[dict] | None = None,
) -> tuple[Any, Any]:
    default = {"sagittal": SAGITTAL, "coronal": CORONAL, "axial": axial_frame(0.0)}[
        view
    ]
    series = SimpleNamespace(
        view=view,
        row=SimpleNamespace(series_uid=uid, fat_suppression="0"),
        slice_thickness_mm=[thickness],
        frames=[default if frame is None else frame],
    )
    record = {
        "series_uid": uid,
        "view": [view.title(), "0", "0"],
        "main_slice": {"object": "fibula"},
        "observations": list(observations or []),
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


def line_of_places(y: float, count: int) -> np.ndarray:
    """One native section's places: a point at (30, y) on each of the first `count` slices' planes."""
    return np.asarray([[30.0, y, 3.0 * z] for z in range(count)])


def leg(tibia: np.ndarray | None = None) -> run.Leg:
    none = np.zeros((0, 3))
    return run.Leg(none, none if tibia is None else tibia, None, None, none)


def scout(
    measured: list[Any],
    sources: list[tuple[Any, Any]],
    mapping: run.MapContext,
    tibia: np.ndarray | None = None,
) -> None:
    """The production call, with stub series standing in for `Measured` and `FibulaFound`."""
    run.fibula_key_planes(
        cast(list[run.Measured], measured),
        mapping,
        cast("list[tuple[run.Measured, run.FibulaFound]]", sources),
        leg(tibia),
        PROOF,
    )


def call(
    measured: list[Any], sources: list[tuple[Any, Any]], tibia=None
) -> run.MapContext:
    mapping = run.MapContext(StudyMap(knee="R"), None, None)
    with run.computing():
        scout(measured, sources, mapping, tibia)
    return mapping


def spy(monkeypatch, name: str) -> list[int]:
    """Count calls of a module-level helper while letting it run."""
    original = getattr(run, name)
    calls: list[int] = []

    def counted(*args, **kwargs):
        calls.append(1)
        return original(*args, **kwargs)

    monkeypatch.setattr(run, name, counted)
    return calls


def row_of(holder: Any, prefix: str, name: str, row: int) -> np.ndarray:
    offsets = holder.arrays[f"{prefix}_offsets"]
    shapes = holder.arrays[f"{prefix}_shapes"]
    flat = holder.arrays[f"{prefix}_{name}"]
    return flat[offsets[row] : offsets[row + 1]].reshape(tuple(shapes[row]))


def summary_of(holder: Any, uid: str) -> dict:
    return holder.record["fibula_key_planes"][uid]


def test_no_native_sources_is_a_named_refusal_with_no_image_work(monkeypatch):
    work = {
        name: spy(monkeypatch, name)
        for name in ("block_medians", "coarse_depth", "leg_on")
    }
    target = axial_target("axial", [8.0, 8.0])

    mapping = call([target], [])

    assert all(not calls for calls in work.values())
    selected = mapping.smap.selected("fibula", "axial")
    assert selected.outcome == rel.REFUSED
    assert "no_native_fibula_sections" in selected.reason
    assert target.arrays == {}
    assert target.record["observations"] == []


def test_an_axial_found_fibula_is_not_a_native_source_and_holds_the_refusal():
    target = axial_target("axial", [8.0])
    own, found = native_source(HOLDER, "axial", line_of_places(30.0, 1))

    mapping = call([target], [(own, found)])

    assert mapping.smap.selected("fibula", "axial").outcome == rel.REFUSED
    refusal = found.record["observations_unresolved"]
    assert [row["series_uid"] for row in refusal] == ["axial"]
    assert refusal[0]["code"].startswith("no_native_fibula_sections")
    assert not any(name.startswith("a4_") for name in found.arrays)


@pytest.mark.parametrize(
    ("frame", "thickness", "code"),
    [
        ("geometry_unreadable: bad header", 3.0, "geometry_unreadable: bad header"),
        (None, None, "source_slice_thickness_unavailable"),
    ],
)
def test_unusable_source_geometry_is_named_and_never_read(
    monkeypatch, frame, thickness, code
):
    work = spy(monkeypatch, "block_medians")
    target = axial_target("axial", [8.0])
    own, found = native_source(
        HOLDER, "sagittal", line_of_places(30.0, 1), frame=frame, thickness=thickness
    )

    mapping = call([target], [(own, found)])

    assert not work
    assert mapping.smap.selected("fibula", "axial").outcome == rel.REFUSED
    said = found.record["observations_unresolved"][0]
    assert said["series_uid"] == "axial"
    assert HOLDER in said["code"] and code in said["code"]
    assert summary_of(found, "axial")["slices_read"] == []


def test_unreadable_axial_geometry_is_not_read_and_implies_no_anatomy():
    unreadable = "geometry_unreadable: bad header"
    target = axial_target(
        "axial",
        [8.0, 8.0, 8.0],
        frames=[axial_frame(0.0), unreadable, axial_frame(6.0)],
        thicknesses=[3.0, 3.0, None],
    )
    own, found = native_source(HOLDER, "sagittal", line_of_places(30.0, 3))

    call([target], [(own, found)])

    summary = summary_of(found, "axial")
    assert summary["slices_read"] == [0]
    assert summary["unreadable_slices"] == {
        unreadable: [1],
        "slice_thickness_unavailable": [2],
    }
    readings = [r for r in found.record["observations"] if r["kind"] == "reading"]
    assert [tuple(r["slices"]) for r in readings] == [(0,)]


def test_wholly_unreadable_axial_series_is_refused_and_a_missing_volume_reads_nothing(
    monkeypatch,
):
    work = spy(monkeypatch, "block_medians")
    bad = axial_target("bad", [8.0, 8.0], frames=["geometry_unreadable: x"] * 2)
    empty = axial_target("empty", [], volume=False)
    no_pixels = axial_target("no_pixels", [])
    own, found = native_source(HOLDER, "sagittal", line_of_places(30.0, 2))

    mapping = call([bad, empty, no_pixels], [(own, found)])

    assert not work
    codes = {
        r["series_uid"]: r["code"] for r in found.record["observations_unresolved"]
    }
    assert "geometry_unreadable: x=2_slices" in codes["bad"]
    assert codes["empty"] == "axial_volume_unavailable"
    assert codes["no_pixels"] == "axial_volume_empty"
    assert mapping.smap.selected("fibula", "axial").outcome == rel.REFUSED


def test_places_off_every_slab_or_off_the_picture_do_no_image_work(monkeypatch):
    work = {
        name: spy(monkeypatch, name)
        for name in ("block_medians", "coarse_depth", "leg_on")
    }
    target = axial_target("axial", [8.0, 8.0])
    far_away = np.asarray([[30.0, 30.0, 500.0]])
    outside_picture = np.asarray([[500.0, 500.0, 0.0], [500.0, 500.0, 3.0]])
    own_a, found_a = native_source("far", "sagittal", far_away)
    own_b, found_b = native_source("outside", "coronal", outside_picture)

    mapping = call([target], [(own_a, found_a), (own_b, found_b)])

    assert all(not calls for calls in work.values())
    summary = summary_of(found_a, "axial")
    assert summary["slices_read"] == []
    assert summary["source_extent_slices"] == [0, 1]
    assert summary["extent_without_in_picture_seed"] == [0, 1]
    assert mapping.smap.selected("fibula", "axial").outcome == rel.REFUSED
    assert not any(name.startswith("a4_") for name in found_a.arrays)


def test_oblique_source_extent_reaches_slabs_its_places_do_not():
    """A source tilted 60 degrees about the left-right axis, 4 mm thick: its voxel reaches 2.433 mm
    along the target's normal from its place (target half thickness 1 mm + 1.433 mm), not 1 mm."""
    tilt = math.radians(60.0)
    oblique = make_frame(
        (0.0, 0.0, 0.0),
        [[1, 0], [0, math.cos(tilt)], [0, math.sin(tilt)]],
    )
    reach = 1.0 + 0.5 * (math.sin(tilt) + math.cos(tilt) * 4.0)
    assert reach == pytest.approx(2.433, abs=1e-3)
    heights = [7.4, 7.6, 9.0, 10.0, 12.4, 12.6]
    target = axial_target(
        "axial",
        [8.0] * len(heights),
        frames=[axial_frame(h) for h in heights],
        thicknesses=[2.0] * len(heights),
    )
    own, found = native_source(
        HOLDER,
        "sagittal",
        np.asarray([[30.0, 30.0, 10.0]]),
        frame=oblique,
        thickness=4.0,
    )

    call([target], [(own, found)])

    expected = [i for i, h in enumerate(heights) if abs(h - 10.0) <= reach]
    assert expected == [1, 2, 3, 4]
    summary = summary_of(found, "axial")
    assert summary["slices_read"] == expected
    assert summary["source_extent_slices"] == expected


def test_oblique_target_slabs_use_each_slices_own_frame():
    tilt = math.radians(30.0)
    basis = [[1, 0], [0, math.cos(tilt)], [0, math.sin(tilt)]]
    normal = np.asarray([0.0, -math.sin(tilt), math.cos(tilt)])
    frames = [make_frame(tuple(normal * (3.0 * i - 4.5)), basis) for i in range(4)]
    centre = frames[1].to_patient(np.asarray([[30.0, 30.0]]))[0]
    place = centre + 0.3 * normal
    target = axial_target("tilted", [8.0] * 4, frames=frames)
    own, found = native_source(HOLDER, "sagittal", place[None, :])

    mapping = call([target], [(own, found)])

    selected = mapping.smap.selected("fibula", "axial")
    assert selected.outcome == rel.SELECTED
    assert np.allclose(selected.normal, frames[1].normal())
    assert np.isclose(selected.offset_mm, frames[1].normal() @ frames[1].origin_lps)
    summary = summary_of(found, "tilted")
    assert summary["slices_read"] == [1]
    prefix = summary["arrays_prefix"]
    pixels = found.arrays[f"{prefix}_native_seed_pixels"]
    assert pixels.tolist() == [[30, 30]]
    assert np.allclose(found.arrays[f"{prefix}_normal_lps"][0], normal)
    assert np.allclose(found.arrays[f"{prefix}_origin_lps"][0], frames[1].origin_lps)


def test_a_section_shared_with_the_tibia_is_refused_not_cut_apart():
    target = axial_target("axial", [8.0])
    own, found = native_source(HOLDER, "sagittal", line_of_places(30.0, 1))
    shared_tibia = np.asarray([[30.0, 33.0, 0.0]])

    mapping = call([target], [(own, found)], tibia=shared_tibia)

    summary = summary_of(found, "axial")
    assert summary["statuses"] == {SHARED: 1}
    assert summary["key_slices"] == []
    assert SHARED in summary["refusal"]
    prefix = summary["arrays_prefix"]
    assert not found.arrays[f"{prefix}_fibula_body"].any()
    assert found.arrays[f"{prefix}_fibula_seeds"].any()
    assert found.arrays[f"{prefix}_tibia_seeds"].any()
    selected = mapping.smap.selected("fibula", "axial")
    assert selected.outcome == rel.REFUSED and SHARED in selected.reason
    reading = next(r for r in found.record["observations"] if r["kind"] == "reading")
    assert reading["code"] == SHARED
    assert reading["support"] == f"{prefix}_fibula_seeds"


def test_a_tibia_elsewhere_leaves_the_section_attributed():
    target = axial_target("axial", [8.0])
    own, found = native_source(HOLDER, "sagittal", line_of_places(30.0, 1))
    elsewhere = np.asarray([[5.0, 5.0, 0.0]])

    mapping = call([target], [(own, found)], tibia=elsewhere)

    summary = summary_of(found, "axial")
    assert summary["statuses"] == {SECTION: 1}
    assert summary["key_slices"] == [0]
    assert mapping.smap.selected("fibula", "axial").outcome == rel.SELECTED


def test_the_largest_section_is_the_key_plane():
    target = axial_target("axial", [6.0, 9.0, 7.0])
    own, found = native_source(HOLDER, "sagittal", line_of_places(30.0, 3))

    mapping = call([target], [(own, found)])

    summary = summary_of(found, "axial")
    prefix = summary["arrays_prefix"]
    areas = found.arrays[f"{prefix}_fibula_area_mm2"]
    assert areas[1] > areas[2] > areas[0] > 0
    assert summary["key_slices"] == [1]
    selected = mapping.smap.selected("fibula", "axial")
    assert (selected.outcome, selected.series_uid, selected.slice) == (
        rel.SELECTED,
        "axial",
        1,
    )


def test_tied_largest_sections_are_all_retained_and_the_map_does_not_pick():
    target = axial_target("axial", [6.0, 9.0, 9.0, 7.0])
    own, found = native_source(HOLDER, "sagittal", line_of_places(30.0, 4))

    mapping = call([target], [(own, found)])

    assert summary_of(found, "axial")["key_slices"] == [1, 2]
    selected = mapping.smap.selected("fibula", "axial")
    assert selected.outcome == rel.TIED
    assert selected.candidates == (("axial", 1), ("axial", 2))


def test_native_sources_share_one_reading_per_series_and_slice(monkeypatch):
    blocks = spy(monkeypatch, "block_medians")
    depth = spy(monkeypatch, "coarse_depth")
    target = axial_target("axial", [8.0, 8.0])
    sagittal = native_source(HOLDER, "sagittal", line_of_places(30.0, 2))
    coronal = native_source("coronal", "coronal", line_of_places(33.0, 2))

    call([target], [sagittal, coronal])

    found = sagittal[1]
    assert len(blocks) == 2 and len(depth) == 2
    summary = summary_of(found, "axial")
    assert summary["source_sections"] == 2
    assert summary["source_points_projected"] == 4
    prefix = summary["arrays_prefix"]
    offsets = found.arrays[f"{prefix}_native_seed_pixel_offsets"]
    pixels = found.arrays[f"{prefix}_native_seed_pixels"]
    for row in range(2):
        held = {tuple(p) for p in pixels[offsets[row] : offsets[row + 1]].tolist()}
        assert held == {(30, 30), (30, 33)}
    assert coronal[1].arrays.keys() == {"a3_fibula_places_lps"}


def test_a_reading_made_for_another_consumer_of_the_plane_is_handed_on(monkeypatch):
    blocks = spy(monkeypatch, "block_medians")
    target = axial_target("axial", [8.0])
    own, found = native_source(HOLDER, "sagittal", line_of_places(30.0, 1))
    second_own, second = native_source("other", "sagittal", line_of_places(30.0, 1))
    mapping = run.MapContext(StudyMap(knee="R"), None, None)

    with run.recording() as led, run.computing():
        for holder_source in ((own, found), (second_own, second)):
            scout([target], [holder_source], mapping)
        names = [event.name for event in led.events()]

    assert len(blocks) == 1
    assert names.count("coarse_axial_blocks.handed_on") == 1
    assert names.count("coarse_axial_depth.handed_on") == 1


def test_multiple_axial_series_keep_distinct_evidence_addresses():
    first = axial_target("axial-one", [6.0, 8.0])
    second = axial_target("axial-two", [9.0, 7.0])
    own, found = native_source(HOLDER, "sagittal", line_of_places(30.0, 2))

    mapping = call([first, second], [(own, found)])

    for uid in ("axial-one", "axial-two"):
        assert summary_of(found, uid)["arrays_prefix"] == f"a4_fibula_coarse_{uid}"
        assert f"a4_fibula_coarse_{uid}_fibula_body" in found.arrays
    assert first.arrays == {} and second.arrays == {}
    assert "fibula_key_planes" not in first.record
    assert "fibula_key_planes" not in second.record
    artifact = str(run.artifact_of(PROOF, found.record))
    readings = [r for r in found.record["observations"] if r["kind"] == "reading"]
    assert len(readings) == 4
    for reading in readings:
        uid = reading["series_uid"]
        assert reading["support"].startswith(f"a4_fibula_coarse_{uid}_")
        assert reading["artifact"] == artifact
        assert tuple(reading["view"]) == ("Axial", "1", "1")
        body = row_of(found, f"a4_fibula_coarse_{uid}", "fibula_body", reading["row"])
        seeds = row_of(found, f"a4_fibula_coarse_{uid}", "fibula_seeds", reading["row"])
        packed = body if reading["support"].endswith("_fibula_body") else seeds
        assert reading["count"] == int(packed.sum())
    selected = mapping.smap.selected("fibula", "axial")
    assert (selected.series_uid, selected.slice) == ("axial-two", 0)
    sources = {c.source for c in mapping.smap.candidates[("fibula", "axial")]}
    assert sources == {"fibula_scout:axial-one", "fibula_scout:axial-two"}


def test_support_rows_are_counted_booleans_with_no_label():
    target = axial_target("axial", [8.0, 8.0])
    own, found = native_source(HOLDER, "sagittal", line_of_places(30.0, 2))

    call([target], [(own, found)])

    readings = [r for r in found.record["observations"] if r["kind"] == "reading"]
    assert [r["row"] for r in readings] == [0, 1]
    for reading in readings:
        assert reading["provenance"] == "native"
        assert reading["object"] == "fibula"
        assert reading["label"] is None
        assert reading["off_plane_mm"] == 0.0
        assert found.arrays[reading["support"]].dtype == np.bool_
        assert reading["count"] is not None and reading["count"] > 0
        assert str(reading["row"]) in reading["note"]
    assert not any(
        r["kind"] == "resolved" and r["support"].startswith("a4_")
        for r in found.record["observations"]
    )


def test_prior_observations_and_inputs_are_preserved():
    prior = {
        "object": "fibula",
        "provenance": "native",
        "kind": "resolved",
        "series_uid": HOLDER,
        "view": ["Sagittal", "0", "0"],
        "slices": [0],
        "code": "identified",
        "count": 12,
        "off_plane_mm": 0.0,
        "support": "a1_objects",
        "note": "the section on this slice, not the whole bone",
        "artifact": "x.npz",
        "row": None,
        "label": 5,
    }
    target = axial_target("axial", [8.0])
    own, found = native_source(
        HOLDER, "sagittal", line_of_places(30.0, 1), observations=[prior]
    )
    found.record["observations_unresolved"] = [
        {
            "object": "fibula",
            "provenance": "laid",
            "series_uid": None,
            "view": None,
            "code": "kept",
        }
    ]
    found.arrays["a1_objects"] = np.arange(6, dtype=np.int8).reshape(2, 3)
    before_arrays = {k: v.copy() for k, v in found.arrays.items()}
    before_places = found.physical.copy()
    before_record = {k: v for k, v in found.record.items() if k != "observations"}

    call([target], [(own, found)])

    assert found.record["observations"][0] == prior
    assert len(found.record["observations"]) == 2
    assert found.record["observations_by_provenance"]["native"] == 2
    assert found.record["observations_unresolved"][0]["code"] == "kept"
    for name, value in before_arrays.items():
        assert np.array_equal(found.arrays[name], value)
    assert np.array_equal(found.physical, before_places)
    for name in ("series_uid", "view", "main_slice", "observations_unresolved"):
        assert found.record[name] == before_record[name]


def test_no_axial_series_is_a_named_refusal_on_the_holder_and_the_map():
    own, found = native_source(HOLDER, "sagittal", line_of_places(30.0, 1))

    mapping = call([own], [(own, found)])

    said = found.record["observations_unresolved"]
    assert [row["code"] for row in said] == ["no_axial_series_for_fibula_key_plane"]
    assert mapping.smap.selected("fibula", "axial").outcome == rel.REFUSED


def test_telemetry_declares_the_selection_and_the_map_as_the_only_consumers():
    target = axial_target("axial", [8.0])
    own, found = native_source(HOLDER, "sagittal", line_of_places(30.0, 1))
    mapping = run.MapContext(StudyMap(knee="R"), None, None)

    with run.recording() as led, run.computing():
        scout([target], [(own, found)], mapping)
        names = {event.name for event in led.events()}

    consumers = {
        n for n in names if ".consumed_by." in n and n.startswith("fibula_key_planes")
    }
    assert consumers == {
        "fibula_key_planes.coarse_sections.consumed_by.fibula_key_slices",
        "fibula_key_planes.key_slices.consumed_by.study_map",
    }


def test_a_refused_scout_hands_no_key_planes_to_the_map_consumer():
    target = axial_target("axial", [8.0])
    own, found = native_source(HOLDER, "sagittal", line_of_places(30.0, 1))
    mapping = run.MapContext(StudyMap(knee="R"), None, None)

    with run.recording() as led, run.computing():
        scout([target], [(own, found)], mapping, np.asarray([[30.0, 33.0, 0.0]]))
        names = {event.name for event in led.events()}

    assert "fibula_key_planes.key_slices.consumed_by.study_map" not in names
    assert "fibula_key_planes.key_slices.produced" not in names
