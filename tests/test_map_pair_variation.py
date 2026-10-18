import csv
import json
from pathlib import Path

import pytest

from knee.collapse.anatomy_map import MAP_OBJECTS
from knee.collapse.relative import ORIENTATIONS
from scripts.map_pair_variation import analyze, write_outputs


def _plane(orientation, coordinate, uid):
    normals = {
        "sagittal": [1.0, 0.0, 0.0],
        "coronal": [0.0, 1.0, 0.0],
        "axial": [0.0, 0.0, 1.0],
    }
    return {
        "orientation": orientation,
        "outcome": "selected",
        "series_uid": f"{uid}-{orientation}",
        "slice": 2,
        "normal": normals[orientation],
        "offset_mm": coordinate[ORIENTATIONS.index(orientation)],
        "precision_mm": 0.5,
        "reason": "synthetic selected plane",
        "provenance": "test fixture",
        "candidates": [],
    }


def _study(uid, points=None, *, construction="three_key_planes", knee="R", scale=100.0):
    points = points or {
        name: (float(i), float(i + 1), float(i + 2))
        for i, name in enumerate(MAP_OBJECTS)
    }
    objects = {}
    for name in MAP_OBJECTS:
        point = points.get(name)
        if point is None:
            objects[name] = {
                "status": "partial",
                "point_lps": None,
                "key_planes": {
                    "sagittal": _plane("sagittal", (0, 0, 0), uid),
                    "coronal": {"outcome": "not_supplied"},
                    "axial": {"outcome": "not_supplied"},
                },
            }
        else:
            objects[name] = {
                "status": "complete",
                "point_lps": list(point),
                "key_planes": {
                    orientation: _plane(orientation, point, uid)
                    for orientation in ORIENTATIONS
                },
            }
    return {
        "schema": "study_map/v1",
        "construction": construction,
        "knee": knee,
        "scale": {"mm": scale, "source": "synthetic"} if scale is not None else None,
        "objects": objects,
    }


def _write_run(tmp_path: Path, maps):
    run = tmp_path / "run"
    run.mkdir()
    (run / "receipt.json").write_text(
        json.dumps({"records": [{"study_uid": uid} for uid in maps]})
    )
    for uid, value in maps.items():
        folder = run / uid
        folder.mkdir()
        if value is not None:
            (folder / "study_map.json").write_text(json.dumps(value))
    return run


def _pair(result, origin, target):
    return next(
        row
        for row in result["pairs"]
        if row["origin"] == origin and row["target"] == target
    )


def test_complete_maps_produce_1806_ordered_pairs_and_sample_statistics(tmp_path):
    a, b = MAP_OBJECTS[:2]
    p1 = {name: (0.0, 0.0, 0.0) for name in MAP_OBJECTS}
    p2 = {name: (0.0, 0.0, 0.0) for name in MAP_OBJECTS}
    p1[b] = (3.0, 4.0, 0.0)
    p2[b] = (6.0, 8.0, 0.0)
    run = _write_run(tmp_path, {"s1": _study("s1", p1), "s2": _study("s2", p2)})

    result = analyze(run)
    pair = _pair(result, a, b)
    assert len(result["pairs"]) == 43 * 42
    assert pair["coverage_studies"] == 2
    assert pair["measured_studies"] == 2
    assert pair["statistics"]["magnitude_mm"] == {
        "n": 2,
        "min": 5.0,
        "max": 10.0,
        "sample_sd": pytest.approx(3.5355339059),
    }
    assert pair["statistics"]["mps_medial_mm"]["sample_sd"] == pytest.approx(
        2.1213203436
    )
    assert pair["statistics"]["normalized_distance"]["min"] == 0.05
    assert (
        result["studies"]["s1"]["positions"][a]["source_planes"]["axial"]["slice"] == 2
    )


def test_partial_position_and_missing_study_are_named_not_zero(tmp_path):
    a, b = MAP_OBJECTS[:2]
    points: dict[str, tuple[float, float, float] | None] = {
        name: (float(i), 0.0, 0.0) for i, name in enumerate(MAP_OBJECTS)
    }
    points[b] = None
    run = _write_run(tmp_path, {"s1": _study("s1", points), "missing": None})

    result = analyze(run)
    pair = _pair(result, a, b)
    assert pair["coverage_studies"] == 2
    assert pair["measured_studies"] == 0
    assert {item["study_uid"] for item in pair["unresolved_studies"]} == {
        "s1",
        "missing",
    }
    partial = result["studies"]["s1"]["positions"][b]
    assert partial["point_lps"] is None
    assert partial["status"] == "partial"


def test_inconsistent_declared_point_is_not_used_for_pair_measurement(tmp_path):
    a, b = MAP_OBJECTS[:2]
    record = _study("s1")
    record["objects"][b]["point_lps"] = [10000.0, 10000.0, 10000.0]
    run = _write_run(tmp_path, {"s1": record})

    result = analyze(run)
    pair = _pair(result, a, b)
    assert pair["measured_studies"] == 0
    assert result["studies"]["s1"]["positions"][b]["construction_consistent"] is False
    assert (
        "declared_position_does_not_match_key_plane_reconstruction"
        in result["studies"]["s1"]["positions"][b]["problems"]
    )


def test_wrong_construction_is_explicit_and_not_measured(tmp_path):
    run = _write_run(
        tmp_path, {"s1": _study("s1", construction="single_section_centroid")}
    )
    result = analyze(run)
    assert result["studies"]["s1"]["status"] == "wrong_construction"
    assert _pair(result, *MAP_OBJECTS[:2])["measured_studies"] == 0


def test_scaleless_and_unknown_knee_preserve_only_supported_metrics(tmp_path):
    a, b = MAP_OBJECTS[:2]
    points = {name: (0.0, 0.0, 0.0) for name in MAP_OBJECTS}
    points[b] = (3.0, 4.0, 0.0)
    run = _write_run(tmp_path, {"s1": _study("s1", points, knee=None, scale=None)})

    result = analyze(run)
    metrics = _pair(result, a, b)["metrics"]
    assert metrics["magnitude_mm"] == [{"study_uid": "s1", "value": 5.0}]
    assert metrics["mps_medial_mm"] == []
    assert metrics["normalized_distance"] == []
    assert _pair(result, a, b)["statistics"]["normalized_distance"]["n"] == 0


def test_coincident_positions_keep_direction_undefined(tmp_path):
    a, b = MAP_OBJECTS[:2]
    points = {name: (0.0, 0.0, 0.0) for name in MAP_OBJECTS}
    run = _write_run(tmp_path, {"s1": _study("s1", points)})

    pair = _pair(analyze(run), a, b)
    assert pair["statistics"]["direction_medial_cosine"]["n"] == 0
    assert pair["statistics"]["magnitude_mm"]["min"] == 0.0


def test_output_json_is_strict_and_csv_has_all_pairs(tmp_path):
    run = _write_run(tmp_path, {"s1": _study("s1")})
    result = analyze(run)
    json_path, csv_path = tmp_path / "result.json", tmp_path / "result.csv"
    write_outputs(result, json_path, csv_path)
    json.loads(json_path.read_text(), parse_constant=lambda token: pytest.fail(token))
    with csv_path.open(newline="") as stream:
        rows = list(csv.DictReader(stream))
    assert len(rows) == 43 * 42
