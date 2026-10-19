"""The study map: key planes -> positions -> all-pairs vectors -> expected slice AND in-plane place (and the axial
bone section that supplies a bone's axial key plane)."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace
from typing import cast

import numpy as np
import pytest

from knee.collapse import relative as rel
from knee.collapse.physical import PlaneFrame
from knee.collapse.study_map import OBJECTS, StudyMap
from scripts import run_interiors as run

SAG = (0, 1, 0, 0, 0, -1)  # normal along x
COR = (1, 0, 0, 0, 0, -1)  # normal along y
AXI = (1, 0, 0, 0, 1, 0)  # normal along z


def frame(orientation, origin, spacing=(1.0, 1.0)):
    return PlaneFrame.from_dicom(origin, orientation, spacing)


def plane(obj, orientation, series, z, f):
    return rel.plane_of_frame(
        obj, orientation, series_uid=series, slice=z, frame=f, precision_mm=1.0
    )


def planes_at(obj, point, series="s"):
    x, y, z = point
    return [
        plane(obj, "sagittal", series + "1", 1, frame(SAG, (x, 0, 0))),
        plane(obj, "coronal", series + "2", 1, frame(COR, (0, y, 0))),
        plane(obj, "axial", series + "3", 1, frame(AXI, (0, 0, z))),
    ]


def build(**points) -> StudyMap:
    m = StudyMap(knee="R")
    for name, point in points.items():
        for p in planes_at(name, point):
            m.offer(name, p, support=100.0, source="test")
    return m


def stack(orientation, origins):
    return [frame(orientation, o) for o in origins]


def test_every_object_has_a_record_and_every_ordered_pair_is_represented():
    m = StudyMap()
    record = m.record()
    assert len(OBJECTS) == 43 and "unassigned" not in OBJECTS
    assert set(record["objects"]) == set(OBJECTS)
    assert all(row["status"] == "partial" for row in record["objects"].values())
    assert record["counts"]["ordered_pairs"] == len(OBJECTS) * (len(OBJECTS) - 1)
    assert record["counts"]["pairs_unresolved"] == len(OBJECTS) * (len(OBJECTS) - 1)
    assert record["counts"]["pairs_complete"] == 0
    row = record["pairs_unresolved"][0]
    assert set(row["unresolved_endpoints"]) == {row["origin"], row["target"]}


def test_complete_and_partial_pairs_are_named_not_dropped():
    m = build(femur=(-10.0, -20.0, 30.0), tibia=(-12.0, -18.0, -5.0))
    m.offer("patella", planes_at("patella", (0, 0, 0))[0], 5.0, "test")
    record = m.record()
    assert record["objects"]["femur"]["point_lps"] == [-10.0, -20.0, 30.0]
    assert record["objects"]["patella"]["status"] == "partial"
    assert record["counts"]["pairs_complete"] == 2
    assert record["counts"]["pairs_complete"] + record["counts"][
        "pairs_unresolved"
    ] == len(OBJECTS) * (len(OBJECTS) - 1)
    pair = {(r["origin"], r["target"]): r for r in record["pairs_complete"]}
    assert pair[("femur", "tibia")]["displacement_lps"] == [-2.0, 2.0, -35.0]
    assert pair[("tibia", "femur")]["displacement_lps"] == [2.0, -2.0, 35.0]
    gone = [
        r
        for r in record["pairs_unresolved"]
        if r["origin"] == "femur" and r["target"] == "patella"
    ]
    assert gone[0]["unresolved_endpoints"] == ["patella"]


def test_no_centroid_substitute_a_missing_plane_gives_no_point():
    m = StudyMap()
    for p in planes_at("femur", (1.0, 2.0, 3.0))[:2]:
        m.offer("femur", p, 1.0, "t")
    got = m.record()["objects"]["femur"]
    assert got["point_lps"] is None and got["status"] == "partial"
    assert got["problems"]["axial"] == rel.NOT_SUPPLIED
    assert got["line_direction"] is not None


def test_series_are_observations_of_one_anatomy_best_supported_plane_wins_and_all_kept():
    m = StudyMap()
    a = planes_at("femur", (0.0, 0.0, 0.0), "fs")[0]
    b = planes_at("femur", (4.0, 0.0, 0.0), "nonfs")[0]
    m.offer("femur", a, 10.0, "fs")
    m.offer("femur", b, 30.0, "nonfs")
    assert m.selected("femur", "sagittal").series_uid == "nonfs1"
    assert len(m.record()["objects"]["femur"]["evidence"]["sagittal"]) == 2


def test_same_physical_plane_is_one_plane_and_equal_distinct_planes_tie():
    m = StudyMap()
    m.offer("femur", planes_at("femur", (2.0, 0, 0), "a")[0], 5.0, "a")
    m.offer("femur", planes_at("femur", (2.0, 0, 0), "b")[0], 9.0, "b")
    assert m.selected("femur", "sagittal").usable
    t = StudyMap()
    t.offer("femur", planes_at("femur", (2.0, 0, 0), "a")[0], 5.0, "a")
    t.offer("femur", planes_at("femur", (7.0, 0, 0), "b")[0], 5.0, "b")
    tied = t.selected("femur", "sagittal")
    assert tied.outcome == rel.TIED and len(tied.candidates) == 2
    assert t.record()["objects"]["femur"]["point_lps"] is None


def test_unknown_object_and_wrong_owner_are_refused():
    m = StudyMap()
    for obj, owner in (("unassigned", "unassigned"), ("femur", "tibia")):
        try:
            m.offer(obj, planes_at(owner, (0, 0, 0))[0])
        except ValueError:
            continue
        raise AssertionError("accepted")


def ideal(origin, target, knee_scale_mm=None):
    table = {
        ("femur", "patella"): (0.0, -30.0, -10.0),
        ("tibia", "patella"): (0.0, -30.0, 35.0),
    }
    v = table.get((origin, target))
    return None if v is None else rel.IdealVector(origin, target, v, f"fake {origin}")


def test_production_anatomy_adapter_passes_the_same_explicit_scale():
    ideal_of, span_of, _ = run.anatomical_reference()
    for scale_mm in (None, 80.0, 160.0):
        vector = ideal_of("femur", "patella", scale_mm)
        expected = run.anatomy_map.ideal_vector("femur", "patella", scale_mm)
        assert vector == expected
        assert span_of("patella", scale_mm) == run.anatomy_map.target_span_mm(
            "patella", scale_mm
        )
    assert ideal_of("unknown", "patella", None) is None
    assert span_of("unknown", None) is None


def test_predictions_are_distinct_per_anchor_with_disagreement_and_residual():
    m = build(femur=(-10.0, -20.0, 30.0), tibia=(-12.0, -18.0, -5.0))
    r = m.record(ideal)
    got = r["objects"]["patella"]
    assert [p["anchor"] for p in got["predictions"]] == ["femur", "tibia"]
    assert got["point_lps"] is None  # a prediction is never a position
    assert got["prediction_disagreement_mm"] is not None
    assert r["objects"]["femur"]["predictions"] == []


def test_guide_gives_native_slice_and_in_plane_place_in_the_series_own_frames():
    m = build(femur=(-10.0, -20.0, 30.0), tibia=(-12.0, -18.0, -5.0))
    # a reversed, unevenly spaced sagittal stack: slice index is never the coordinate
    xs = [-40.0, -15.0, -12.0, -10.0, 0.0]
    frames = stack(SAG, [(x, -60.0, 60.0) for x in xs][::-1])
    g = m.guide("patella", "sag", frames, (200, 200), ideal)
    assert g.status == "guided" and g.anchors == ("femur", "tibia")
    assert all(0 <= z < len(frames) for z in g.slices)
    assert g.spread_mm and g.spread_mm > 0
    assert len(g.rcs) == 2 and g.rcs[0][1] != g.rcs[1][1]
    nearest_x = frames[g.rcs[0][0]].origin_lps[0]
    assert nearest_x in (-12.0, -10.0)


def test_guide_unguided_names_its_reason():
    m = StudyMap(knee="R")
    got = m.guide("patella", "s", [], None, None)
    assert got.status == "unguided:no_anatomical_ideal_supplied"
    got = m.guide("patella", "s", [], None, ideal)
    assert got.status == "unguided:no_complete_anchor_with_an_ideal"
    m = build(femur=(0.0, 0.0, 0.0))
    frames = stack(SAG, [(0, 0, 0)])
    assert m.guide("patella", "s", frames, (10, 10), None).status.startswith(
        "unguided:"
    )
    assert StudyMap(knee=None).predictions(ideal)["patella"] == []


def test_unknown_knee_gives_no_expected_point_never_a_guess():
    m = StudyMap(knee=None)
    for p in planes_at("femur", (0.0, 0.0, 0.0)):
        m.offer("femur", p, 1.0, "t")
    got = m.predictions(ideal)["patella"][0]
    assert got.status == "knee_unknown" and got.point_lps is None


def test_refinement_adds_an_anchor_and_is_logged_and_prediction_use_is_counted():
    m = build(femur=(-10.0, -20.0, 30.0))
    assert len(m.predictions(ideal)["patella"]) == 1
    m.refine(
        "tibia", [(p, 50.0, "joint") for p in planes_at("tibia", (-12.0, -18.0, -5.0))]
    )
    assert len(m.predictions(ideal)["patella"]) == 2
    m.note_use("patella", "s", "guided_hit", slices=3)
    m.note_use("patella", "s", "guided_miss_then_full_search")
    r = m.record(ideal)
    assert r["counts"]["refinements"] == 1
    assert r["counts"]["uses"] == {
        "guided_hit": 1,
        "guided_miss_then_full_search": 1,
    }


def ring(dark_inside: bool):
    img = np.full((60, 60), 100.0)
    yy, xx = np.mgrid[:60, :60]
    r = np.hypot(yy - 30, xx - 30)
    img[r <= 15] = 40.0 if dark_inside else 160.0  # marrow
    img[(r > 15) & (r <= 17)] = 5.0  # cortex, dark on every sequence
    if dark_inside:
        img[(r > 17) & (r <= 20)] = 200.0  # bright rim (cartilage / fluid)
    return img


# ---- the real driver: the map is built before the families search, and they consume it


FRAME60 = PlaneFrame(
    np.zeros(3), np.array([[0.0, 1.0], [1.0, 0.0], [0.0, 0.0]]), (1.0, 1.0)
)
PROOF = "1.2.826.0.1.3680043.8.498.10095687747295410396510538520594649149"
ROOT = Path(__file__).resolve().parent.parent


def test_the_map_is_built_after_the_bones_and_before_every_other_family_in_the_driver():
    import ast

    tree = ast.parse((ROOT / "scripts/run_interiors.py").read_text())
    body = next(
        n
        for n in tree.body
        if isinstance(n, ast.FunctionDef) and n.name == "measure_study"
    )
    calls = [
        (n.lineno, n.func.id)
        for n in ast.walk(body)
        if isinstance(n, ast.Call) and isinstance(n.func, ast.Name)
    ]
    first = {}
    for line, name in sorted(calls):
        first.setdefault(name, line)
    assert first["name_the_bones"] < first["build_study_map"]
    for family in ("name_the_patella", "name_the_joint", "name_the_recess"):
        assert first["build_study_map"] < first[family]
    assert first["finish_map"] > first["posterior_silences"]
    patella = next(
        n
        for n in ast.walk(body)
        if isinstance(n, ast.Call)
        and isinstance(n.func, ast.Name)
        and n.func.id == "name_the_patella"
    )
    assert len(patella.args) == 6  # the map is handed to the patella's search


def test_production_search_reads_the_map_not_the_cohort_window():
    series = SimpleNamespace(volume=np.zeros((9, 4, 4)))
    own = SimpleNamespace(series=series, record={"slice_index": 4})
    guide = run.Guide(
        "patella", "s", "guided", (2, 3), anchors=("femur",), spread_mm=1.0
    )
    window, said = run.patella_neighbourhood(
        cast(run.Measured, own), "no_reference", guide
    )
    assert said["code"] == "map_window" and window is not None
    assert list(np.flatnonzero(window)) == [2, 3, 4]  # the middle slice is always in
    # a map that cannot guide reads the whole depth, with its reason; the cohort window is not used
    cold = run.Guide("patella", "s", "unguided:no_complete_anchor_with_an_ideal")
    window, said = run.patella_neighbourhood(
        cast(run.Measured, own), "no_reference", cold
    )
    assert window is None and said["code"].startswith("map_unguided:")


def test_refinement_takes_native_resolved_sections_never_bones_or_diffuse_and_never_twice(
    monkeypatch,
):
    monkeypatch.setattr(run, "plane_frame", lambda series, z: FRAME60)
    series = SimpleNamespace(
        row=SimpleNamespace(series_uid="ax"), slice_thickness_mm=[3.0, 3.0]
    )
    rows = [
        {
            "object": name,
            "provenance": prov,
            "kind": kind,
            "series_uid": "ax",
            "view": ["Axial", "1", "1"],
            "slices": [1],
            "count": 50,
            "code": "identified",
        }
        for name, prov, kind in (
            ("patella", "native", "resolved"),
            ("femur", "native", "resolved"),
            ("air", "native", "resolved"),
            ("sartorius", "laid", "resolved"),
            ("gracilis", "projected", "target"),
        )
    ]
    own = SimpleNamespace(
        series=series, record={"view": ["Axial", "1", "1"], "observations": rows}
    )
    context = run.MapContext(StudyMap(knee="R"), None, None, diffuse={"air"})
    assert run.refine_map(context, [cast(run.Measured, own)]) == 1
    assert run.refine_map(context, [cast(run.Measured, own)]) == 0
    got = context.smap.record()["objects"]
    assert got["patella"]["key_planes"]["axial"]["outcome"] == "selected"
    assert got["patella"]["status"] == "partial"
    for name in ("femur", "air", "sartorius", "gracilis"):
        assert got[name]["key_planes"]["axial"]["outcome"] == "not_supplied"


def test_refinement_keeps_later_planes_from_the_same_series_and_equal_ties(monkeypatch):
    frames = [frame(AXI, (0.0, 0.0, float(z))) for z in range(3)]
    monkeypatch.setattr(run, "plane_frame", lambda series, z: frames[z])
    series = SimpleNamespace(
        row=SimpleNamespace(series_uid="ax"), slice_thickness_mm=[1.0] * 3
    )

    def observation(z, count):
        return {
            "object": "patella",
            "provenance": "native",
            "kind": "resolved",
            "series_uid": "ax",
            "slices": [z],
            "count": count,
            "code": "identified",
        }

    rows = [observation(0, 10)]
    own = SimpleNamespace(
        series=series, record={"view": ["Axial", "1", "1"], "observations": rows}
    )
    context = run.MapContext(StudyMap(knee="R"), None, None)
    assert run.refine_map(context, [cast(run.Measured, own)]) == 1
    rows.append(observation(1, 20))
    assert run.refine_map(context, [cast(run.Measured, own)]) == 1
    assert context.smap.selected("patella", "axial").slice == 1
    rows.append(observation(2, 20))
    assert run.refine_map(context, [cast(run.Measured, own)]) == 1
    assert context.smap.selected("patella", "axial").outcome == rel.TIED
    version = context.smap.version
    assert run.refine_map(context, [cast(run.Measured, own)]) == 0
    assert context.smap.version == version
    assert len(context.smap.candidates[("patella", "axial")]) == 3


def test_axial_bone_planes_seed_from_the_carried_line_and_offer_the_largest_section(
    monkeypatch,
):
    volume = np.stack([ring(True), ring(True), np.full((60, 60), 50.0)])
    line = np.zeros((60, 60), dtype=bool)
    line[25:36, 30] = True
    nothing = np.zeros((60, 60), dtype=bool)
    monkeypatch.setattr(
        run, "plane_frame", lambda series, z: frame(AXI, (0.0, 0.0, 3.0 * z))
    )
    monkeypatch.setattr(
        run, "leg_on", lambda leg, series, z, frame, shape, thick: (line, nothing)
    )
    series = SimpleNamespace(
        row=SimpleNamespace(series_uid="ax", fat_suppression="1"),
        volume=volume,
        slice_thickness_mm=[3.0, 3.0, 3.0],
    )
    own = SimpleNamespace(
        series=series,
        arrays={"acquired_plane": volume[1]},
        record={"view": ["Axial", "1", "1"]},
    )
    smap = StudyMap(knee="R")
    leg = SimpleNamespace(
        femur_lps=np.array([[0.0, 0.0, 100.0]]),
        tibia_lps=np.array([[0.0, 0.0, -100.0]]),
    )
    said = run.axial_bone_planes(smap, cast(run.Measured, own), cast(run.Leg, leg))
    assert said["femur"]["key_slices"] == [
        0,
        1,
    ]  # equal sections: both kept, none broken
    assert said["tibia"]["key_slices"] == [] and not said["tibia"]["statuses"]
    assert smap.selected("femur", "axial").outcome == rel.TIED
    assert smap.selected("tibia", "axial").outcome == rel.NOT_SUPPLIED
    assert "a4_axial_femur_section_area_mm2" in own.arrays


def test_nothing_is_drawn_or_plotted_without_the_flag():
    code = (
        "import sys; sys.path.insert(0, 'src'); sys.path.insert(0, '.');"
        "import scripts.run_interiors, knee.collapse.study_map, knee.collapse.coarse_section;"
        "assert 'matplotlib' not in sys.modules, 'plotting library loaded'"
    )
    done = subprocess.run(
        [sys.executable, "-c", code],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert done.returncode == 0, done.stderr


@pytest.mark.skipif(not (ROOT / "data/raw").is_dir(), reason="competition files absent")
def test_real_entry_point_builds_the_map_and_the_patella_reads_it(
    tmp_path, monkeypatch
):
    corpus = run.opened(ROOT / "data/raw")
    if PROOF not in corpus.tables.studies:
        pytest.skip("proof study absent")

    def forbidden_legacy_reference(*_args):
        raise AssertionError(
            "the production map must not compute the unused single-bone reference"
        )

    monkeypatch.setattr(
        run, "select_reference", forbidden_legacy_reference, raising=False
    )
    result = run.measure_study(
        corpus, PROOF, tmp_path / "run", tmp_path / "main", False
    )
    counts = result["study_map"]
    assert set(result["objects"]) == set(run.MAP_NAMES)
    assert all(
        value["observations"] or value["unresolved"]
        for value in result["objects"].values()
    )
    assert counts["objects"] == len(run.MAP_NAMES)
    assert counts["pairs_complete"] + counts["pairs_unresolved"] == len(OBJECTS) * (
        len(OBJECTS) - 1
    )
    assert counts["complete"] >= 2 and counts["predictions"] > 0
    assert set(counts["uses"]) >= {"guided_hit"} or any(
        k.startswith("guided_miss") for k in counts["uses"]
    )
    full = json.loads((tmp_path / "run" / PROOF / "study_map.json").read_text())
    assert not any("centroid" in key for key in json.dumps(full).split('"'))
    assert full["objects"]["femur"]["key_planes"]["axial"]["outcome"] == "selected"
    # every ordered pair is a complete vector or a named unresolved end
    assert len(full["pairs_complete"]) + len(full["pairs_unresolved"]) == len(
        OBJECTS
    ) * (len(OBJECTS) - 1)
    patella = next(
        r["patella"]
        for r in result["records"]
        if r.get("patella", {}).get("search", {}).get("code") == "map_window"
    )
    assert patella["search"]["anchors"] and patella["outcome"] == "identified"
    # Native axial recess fluid joins the existing sagittal/coronal sections before
    # later searches; the output is real boolean support, never a projected boundary.
    fluid = full["objects"]["joint_fluid"]
    assert fluid["status"] == "complete"
    assert all(p["outcome"] == "selected" for p in fluid["key_planes"].values())
    assert any(
        "joint_fluid"
        in record.get("main_slice", {}).get("map_guidance", {}).get("anchors", [])
        for record in result["main_records"]
    )
    native_fluid = [
        row
        for record in [*result["records"], *result["main_records"]]
        for row in record.get("observations", [])
        if row["object"] == "joint_fluid"
        and row["support"] == "a4_axial_joint_fluid"
        and row["provenance"] == "native"
        and row["kind"] == "resolved"
    ]
    assert {row["slices"][0] for row in native_fluid} >= {21, 22}
    assert all(row["count"] > 0 and row["label"] is None for row in native_fluid)
    native_axial_anterior = [
        row
        for record in [*result["records"], *result["main_records"]]
        for row in record.get("observations", [])
        if row["object"] == "anterior_synovial_recess"
        and row["support"] == "a4_axial_joint_fluid"
        and row["provenance"] == "native"
        and row["kind"] == "resolved"
        and row["view"][0] == "Axial"
    ]
    assert len(native_axial_anterior) == len(native_fluid) == 2
    shared_address_fields = (
        "kind",
        "provenance",
        "view",
        "support",
        "series_uid",
        "artifact",
        "row",
        "slices",
        "count",
        "label",
        "code",
    )
    for fluid_row in native_fluid:
        matches = [
            row
            for row in native_axial_anterior
            if (row["series_uid"], row["slices"], row["row"])
            == (fluid_row["series_uid"], fluid_row["slices"], fluid_row["row"])
        ]
        assert len(matches) == 1
        anterior_row = matches[0]
        assert {field: anterior_row[field] for field in shared_address_fields} == {
            field: fluid_row[field] for field in shared_address_fields
        }
        artifact = Path(fluid_row["artifact"])
        artifact_path = next(
            root / artifact
            for root in (tmp_path / "run", tmp_path / "main")
            if (root / artifact).is_file()
        )
        with np.load(artifact_path, allow_pickle=False) as saved:
            support = saved[fluid_row["support"]]
            assert support.dtype == np.bool_
            if fluid_row["row"] is None:
                assert support.ndim == 2
                mask = support
            else:
                assert support.ndim == 3
                assert 0 <= fluid_row["row"] < support.shape[0]
                mask = support[fluid_row["row"]]
            assert int(mask.sum()) == fluid_row["count"]

    anterior_map = full["objects"]["anterior_synovial_recess"]
    anterior_planes = anterior_map["key_planes"]
    assert anterior_planes["sagittal"]["outcome"] == "selected"
    assert anterior_planes["axial"]["outcome"] == "selected"
    assert anterior_planes["coronal"]["outcome"] == "selected"
    # Scope/source changes may move key planes. Every selected plane must still
    # come from a native resolved observation, not a projected expectation.
    native_anterior = [
        row
        for record in [*result["records"], *result["main_records"]]
        for row in record.get("observations", [])
        if row["object"] == "anterior_synovial_recess"
        and row["provenance"] == "native"
        and row["kind"] == "resolved"
    ]
    for orientation, plane in anterior_planes.items():
        assert any(
            row["series_uid"] == plane["series_uid"]
            and tuple(row["slices"]) == (plane["slice"],)
            and row["view"][0].casefold() == orientation
            for row in native_anterior
        )
    assert anterior_map["status"] == "complete"
    assert np.isfinite(np.asarray(anterior_map["point_lps"], dtype=float)).all()
    native_coronal_anterior = [
        row
        for record in result["records"]
        for row in record.get("observations", [])
        if row["object"] == "anterior_synovial_recess"
        and row["provenance"] == "native"
        and row["kind"] == "resolved"
        and row["view"][0].casefold() == "coronal"
    ]
    assert len(native_coronal_anterior) == 1
    row = native_coronal_anterior[0]
    assert row["support"] == "a4_coronal_anterior_recess" and row["label"] is None
    assert tuple(row["slices"]) == (anterior_planes["coronal"]["slice"],)
    assert row["row"] == 0
    with np.load(tmp_path / "run" / row["artifact"], allow_pickle=False) as saved:
        native_mask = saved[row["support"]][row["row"]]
        location = saved["a4_coronal_anterior_target"][row["row"]]
        white = saved["a4_coronal_anterior_white"][row["row"]]
        assert native_mask.dtype == np.bool_
        assert int(native_mask.sum()) == row["count"] > int(location.sum())
        assert np.any(native_mask & location) and np.all(native_mask <= white)
    assert any(
        use["object"] == "anterior_synovial_recess"
        and use.get("question") == "coronal_anterior_recess"
        for use in full["uses"]
    )
    assert len(anterior_map["evidence"]["axial"]) >= 2
    assert any(
        refinement["object"] == "anterior_synovial_recess"
        and "axial" in refinement["orientations"]
        for refinement in full["refinements"]
    )
    assert not any(
        "anterior_synovial_recess" in pair["unresolved_endpoints"]
        for pair in full["pairs_unresolved"]
    )

    capsule_object = full["objects"]["joint_capsule"]
    capsule_planes = capsule_object["key_planes"]
    assert capsule_planes["axial"]["outcome"] == "selected"
    assert capsule_planes["coronal"]["outcome"] == "selected"
    assert capsule_planes["sagittal"]["outcome"] == "selected"
    assert capsule_object["status"] == "complete"
    assert np.isfinite(np.asarray(capsule_object["point_lps"], dtype=float)).all()
    sagittal_walls = [
        row
        for record in result["records"]
        for row in record.get("observations", [])
        if row["object"] == "joint_capsule"
        and row["provenance"] == "native"
        and row["kind"] == "resolved"
        and row["view"][0].casefold() == "sagittal"
    ]
    assert sagittal_walls
    for wall in sagittal_walls:
        assert wall["support"] == "a4_sagittal_capsule_outer_wall"
        assert wall["label"] is None and wall["row"] is not None
        with np.load(tmp_path / "run" / wall["artifact"], allow_pickle=False) as saved:
            slot = wall["row"]
            native_wall = saved[wall["support"]][slot]
            body = saved["a4_sagittal_capsule_body"][slot]
            available = saved["a4_sagittal_capsule_available"][slot]
            assert native_wall.dtype == np.bool_
            assert int(native_wall.sum()) == wall["count"] > 0
            assert np.all(native_wall <= available)
            assert not np.any(native_wall & body)
            assert int(saved["a4_sagittal_capsule_slices"][slot]) == wall["slices"][0]
            assert "a4_sagittal_capsule_body_outer_edge" in saved.files
    assert any(
        use["object"] == "joint_capsule" and use.get("question") == "sagittal_capsule"
        for use in full["uses"]
    )

    native_capsule = [
        row
        for record in [*result["records"], *result["main_records"]]
        for row in record.get("observations", [])
        if row["object"] == "joint_capsule"
        and row["provenance"] == "native"
        and row["kind"] == "resolved"
        and row["view"][0] == "Axial"
    ]
    expected_capsule_supports = {
        ("a3_recess_plane_medial_wall", 21): (65, True),
        ("a3_recess_plane_lateral_wall", 21): (71, True),
        ("a2_medial_patellar_retinaculum", 22): (70, False),
        ("a2_lateral_patellar_retinaculum", 22): (65, False),
    }
    assert len(native_capsule) == len(expected_capsule_supports)
    assert {(row["support"], row["slices"][0]) for row in native_capsule} == set(
        expected_capsule_supports
    )
    for row in native_capsule:
        expected_count, pointed = expected_capsule_supports[
            (row["support"], row["slices"][0])
        ]
        assert tuple(row["view"]) == ("Axial", "1", "1")
        assert Path(row["artifact"]).parts[0] == PROOF
        assert Path(row["artifact"]).name.startswith(row["series_uid"])
        assert row["count"] == expected_count and row["label"] is None
        if pointed:
            assert row["row"] is not None and row["row"] >= 0
        else:
            assert row["row"] is None
        artifact = Path(row["artifact"])
        roots = (tmp_path / "run", tmp_path / "main")
        artifact_path = next(
            root / artifact for root in roots if (root / artifact).is_file()
        )
        with np.load(artifact_path, allow_pickle=False) as saved:
            support = saved[row["support"]]
            if pointed:
                assert support.dtype == np.bool_ and support.ndim == 3
                assert row["row"] < support.shape[0]
                mask = support[row["row"]]
            else:
                assert support.dtype == np.bool_ and support.ndim == 2
                mask = support
            assert int(mask.sum()) == row["count"]

    original_walls = [
        row
        for record in result["records"]
        for row in record.get("observations", [])
        if row["object"]
        in ("medial_patellar_retinaculum", "lateral_patellar_retinaculum")
        and row["provenance"] == "native"
        and row["kind"] == "resolved"
        and row["view"][0] == "Axial"
        and tuple(row["slices"]) == (21,)
    ]
    assert len(original_walls) == 2
    expected_original_walls = {
        "medial_patellar_retinaculum": (
            65,
            "a3_recess_plane_medial_wall",
            0,
            None,
        ),
        "lateral_patellar_retinaculum": (
            71,
            "a3_recess_plane_lateral_wall",
            0,
            None,
        ),
    }
    for row in original_walls:
        count, support_name, source_row, label = expected_original_walls[row["object"]]
        assert (
            row["count"],
            row["support"],
            row["row"],
            row["label"],
            tuple(row["slices"]),
            tuple(row["view"]),
        ) == (count, support_name, source_row, label, (21,), ("Axial", "1", "1"))
        assert row["artifact"] == (
            f"{PROOF}/"
            "1.2.826.0.1.3680043.8.498.67495435033389756963800730529101229430.npz"
        )

    synovium_object = full["objects"]["synovium"]
    synovium_planes = synovium_object["key_planes"]
    assert synovium_object["status"] == "complete"
    assert all(plane["outcome"] == "selected" for plane in synovium_planes.values())
    point_lps = np.asarray(synovium_object["point_lps"], dtype=float)
    assert point_lps.shape == (3,) and np.all(np.isfinite(point_lps))

    native_lining = [
        row
        for record in [*result["records"], *result["main_records"]]
        for row in record.get("observations", [])
        if row["object"] == "synovium"
        and row["provenance"] == "native"
        and row["kind"] == "resolved"
        and row["view"][0] == "Axial"
    ]
    expected_lining_supports = {
        ("a3_recess_plane_medial_lining", 21): (
            "a3_recess_plane_medial_recess",
            "a3_recess_plane_medial_wall",
            0,
        ),
        ("a3_recess_plane_lateral_lining", 21): (
            "a3_recess_plane_lateral_recess",
            "a3_recess_plane_lateral_wall",
            0,
        ),
        ("a2_retinacula_positive_inner_lining", 22): (
            "a2_retinacula_positive_inner_selected_recess",
            "a2_medial_patellar_retinaculum",
            None,
        ),
        ("a2_retinacula_negative_inner_lining", 22): (
            "a2_retinacula_negative_inner_selected_recess",
            "a2_lateral_patellar_retinaculum",
            None,
        ),
    }
    assert len(native_lining) == len(expected_lining_supports)
    assert {(row["support"], row["slices"][0]) for row in native_lining} == set(
        expected_lining_supports
    )
    for row in native_lining:
        pocket_name, wall_name, expected_row = expected_lining_supports[
            (row["support"], row["slices"][0])
        ]
        assert tuple(row["view"]) == ("Axial", "1", "1")
        assert Path(row["artifact"]).parts[0] == PROOF
        assert Path(row["artifact"]).name.startswith(row["series_uid"])
        assert row["row"] == expected_row
        assert row["label"] is None and row["count"] > 0
        artifact = Path(row["artifact"])
        roots = (tmp_path / "run", tmp_path / "main")
        artifact_path = next(
            root / artifact for root in roots if (root / artifact).is_file()
        )
        with np.load(artifact_path, allow_pickle=False) as saved:

            def read_boolean_support(name, row_index):
                values = saved[name]
                if row_index is None:
                    assert values.dtype == np.bool_ and values.ndim == 2
                    return values
                assert values.dtype == np.bool_ and values.ndim == 3
                assert row_index < values.shape[0]
                return values[row_index]

            lining_mask = read_boolean_support(row["support"], row["row"])
            pocket_mask = read_boolean_support(pocket_name, expected_row)
            wall_mask = read_boolean_support(wall_name, expected_row)
            assert lining_mask.shape == pocket_mask.shape == wall_mask.shape
            assert int(lining_mask.sum()) == row["count"]
            assert np.all(lining_mask <= pocket_mask)
            assert not np.any(lining_mask & wall_mask)

    native_synovium = [
        row
        for record in [*result["records"], *result["main_records"]]
        for row in record.get("observations", [])
        if row["object"] == "synovium"
        and row["provenance"] == "native"
        and row["kind"] == "resolved"
    ]
    for orientation, plane in synovium_planes.items():
        assert any(
            row["series_uid"] == plane["series_uid"]
            and tuple(row["slices"]) == (plane["slice"],)
            and row["view"][0].casefold() == orientation
            for row in native_synovium
        )
    normals = np.asarray(
        [plane["normal"] for plane in synovium_planes.values()], dtype=float
    )
    assert np.linalg.matrix_rank(normals) == 3

    coronal_lining = [
        row
        for row in result["records"]
        for row in row.get("observations", [])
        if row["object"] == "synovium"
        and row["provenance"] == "native"
        and row["kind"] == "resolved"
        and row["view"][0].casefold() == "coronal"
        and row["support"] == "a4_coronal_lining"
    ]
    assert len(coronal_lining) == 1
    lining_row = coronal_lining[0]
    assert lining_row["row"] is None and lining_row["label"] is None
    assert lining_row["count"] > 0
    coronal_record = next(
        record
        for record in result["records"]
        if record["series_uid"] == lining_row["series_uid"]
        and record["view"][0].casefold() == "coronal"
    )
    assert (
        coronal_record["assignments"]["codes"]["synovium"]
        == "abstain_not_a_sagittal_slice"
    )
    coronal_capsule = [
        row
        for row in coronal_record["observations"]
        if row["object"] == "joint_capsule"
        and row["provenance"] == "native"
        and row["kind"] == "resolved"
        and row["support"] == "a2_joint_capsule"
    ]
    assert len(coronal_capsule) == 1
    assert coronal_record["observations"].index(coronal_capsule[0]) < coronal_record[
        "observations"
    ].index(lining_row)
    artifact = Path(lining_row["artifact"])
    coronal_artifact = tmp_path / "run" / artifact
    with np.load(coronal_artifact, allow_pickle=False) as saved:
        old_lining = saved["a2_synovium"]
        new_lining = saved["a4_coronal_lining"]
        capsule_mask = saved["a2_joint_capsule"]
        assert old_lining.dtype == new_lining.dtype == capsule_mask.dtype == np.bool_
        assert not old_lining.any()
        assert int(new_lining.sum()) == lining_row["count"]
        assert int(capsule_mask.sum()) == coronal_capsule[0]["count"]
    assert not (tmp_path / "pictures").exists()


def test_a_bones_axial_section_is_not_attributed_inside_the_other_bones_native_extent(
    monkeypatch,
):
    # the tibia's carried line lies in a body at the joint that is the femur's: only slices wholly below
    # the femur's lowest carried place are the tibia's; the overlap is named, never attributed
    volume = np.stack([ring(True)] * 3)
    line = np.zeros((60, 60), dtype=bool)
    line[25:36, 30] = True
    nothing = np.zeros((60, 60), dtype=bool)
    monkeypatch.setattr(
        run, "plane_frame", lambda series, z: frame(AXI, (0.0, 0.0, 3.0 * z))
    )
    monkeypatch.setattr(
        run, "leg_on", lambda leg, series, z, frame, shape, thick: (nothing, line)
    )
    series = SimpleNamespace(
        row=SimpleNamespace(series_uid="ax", fat_suppression="1"),
        volume=volume,
        slice_thickness_mm=[3.0, 3.0, 3.0],
    )
    own = SimpleNamespace(
        series=series,
        arrays={"acquired_plane": volume[1]},
        record={"view": ["Axial", "1", "1"]},
    )
    leg = SimpleNamespace(
        femur_lps=np.array([[0.0, 0.0, 2.0]]), tibia_lps=np.array([[0.0, 0.0, 9.0]])
    )
    said = run.axial_bone_planes(
        StudyMap(knee="R"), cast(run.Measured, own), cast(run.Leg, leg)
    )
    assert said["tibia"]["key_slices"] == [0]
    assert said["tibia"]["statuses"][run.AXIAL_OVERLAP] == 2
