"""Summarize measured pair-vector variation across saved three-plane study maps.

This reports observed study measurements only. It does not construct anatomical
ideals, central values, or search windows.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
from pathlib import Path
from typing import Any

import numpy as np

from knee.collapse import relative as rel
from knee.collapse.anatomy_map import MAP_OBJECTS


def unwrap_record(value: Any) -> dict[str, Any] | None:
    if not isinstance(value, dict):
        return None
    if value.get("schema") == "study_map/v1":
        return value
    for key in ("currentStudyMap", "current_study_map"):
        wrapped = value.get(key)
        if isinstance(wrapped, dict) and isinstance(wrapped.get("record"), dict):
            return wrapped["record"]
    if isinstance(value.get("record"), dict):
        return value["record"]
    return None


def _parse_plane(object_name: str, orientation: str, data: Any) -> rel.KeyPlane:
    if not isinstance(data, dict):
        return rel.invalid_plane(object_name, orientation, "record_not_object")
    outcome = data.get("outcome")
    if outcome == rel.SELECTED:
        return rel.key_plane(
            object_name,
            orientation,
            series_uid=str(data.get("series_uid", "")),
            slice=int(data.get("slice", -1)),
            normal=data.get("normal"),
            offset_mm=data.get("offset_mm"),
            precision_mm=data.get("precision_mm")
            if data.get("precision_mm") is not None
            else math.nan,
            reason=str(data.get("reason", "")),
            provenance=str(data.get("provenance", "")),
        )
    if outcome in rel.UNRESOLVED_OUTCOMES:
        return rel.unresolved_plane(
            object_name,
            orientation,
            outcome,
            reason=str(data.get("reason", "")),
            provenance=str(data.get("provenance", "")),
            candidates=data.get("candidates", ()),
        )
    code = str(outcome or "missing_outcome")
    return rel.invalid_plane(object_name, orientation, code.removeprefix("invalid:"))


def _scale(record: dict[str, Any]) -> rel.KneeScale:
    value = record.get("scale", record.get("knee_scale"))
    source = "study_map"
    if isinstance(value, dict):
        source = str(value.get("source", source))
        value = value.get("mm")
    return rel.knee_scale(value, source) if value is not None else rel.UNKNOWN_SCALE


def _position_record(name: str, data: Any) -> tuple[rel.Position, dict[str, Any]]:
    problems: list[str] = []
    if not isinstance(data, dict):
        data = {}
        problems.append("object_record_missing_or_invalid")
    planes_data = data.get("key_planes")
    if not isinstance(planes_data, dict):
        planes_data = {}
        problems.append("key_planes_missing_or_invalid")
    planes = [
        _parse_plane(name, orientation, planes_data.get(orientation))
        for orientation in rel.ORIENTATIONS
    ]
    position = rel.reference_position(name, planes)
    declared_status = data.get("status")
    declared_point = data.get("point_lps")
    consistent = declared_status == position.status
    if position.complete:
        try:
            consistent = consistent and np.allclose(
                np.asarray(declared_point, dtype=float),
                np.asarray(position.point_lps, dtype=float),
                rtol=1e-12,
                atol=1e-8,
            )
        except (TypeError, ValueError):
            consistent = False
    if not consistent:
        problems.append("declared_position_does_not_match_key_plane_reconstruction")
    return position, {
        "status": position.status,
        "point_lps": list(position.point_lps)
        if position.point_lps is not None
        else None,
        "source_planes": {plane.orientation: plane.address() for plane in planes},
        "problems": problems,
        "construction_consistent": bool(consistent),
    }


def _stats(values: list[float]) -> dict[str, Any]:
    if not values:
        return {"n": 0, "min": None, "max": None, "sample_sd": None}
    return {
        "n": len(values),
        "min": min(values),
        "max": max(values),
        "sample_sd": float(np.std(values, ddof=1)) if len(values) >= 2 else None,
    }


METRICS = (
    "mps_medial_mm",
    "mps_posterior_mm",
    "mps_superior_mm",
    "magnitude_mm",
    "normalized_distance",
    "direction_medial_cosine",
    "direction_posterior_cosine",
    "direction_superior_cosine",
    "normalized_medial_component",
    "normalized_posterior_component",
    "normalized_superior_component",
)


def _measure_pair(
    a: rel.Position, b: rel.Position, scale: rel.KneeScale, knee: str | None
) -> tuple[dict[str, float], dict[str, str]]:
    vector = rel.pair_vector(a, b, scale, knee)
    measured: dict[str, float] = {}
    reasons: dict[str, str] = {}
    anatomical = vector.anatomical_mm
    if anatomical is None:
        reasons.update(
            {key: "knee_unknown" for key in METRICS[:3] + METRICS[5:8] + METRICS[8:11]}
        )
    else:
        for key, value in zip(METRICS[:3], anatomical, strict=True):
            measured[key] = float(value)
        if vector.magnitude_mm == 0:
            reasons.update(
                {key: "coincident_points_direction_undefined" for key in METRICS[5:8]}
            )
        else:
            for key, value in zip(
                METRICS[5:8], (x / vector.magnitude_mm for x in anatomical), strict=True
            ):
                measured[key] = float(value)
        if scale.mm is None:
            reasons.update({key: scale.code for key in METRICS[8:11]})
        else:
            for key, value in zip(
                METRICS[8:11], (x / scale.mm for x in anatomical), strict=True
            ):
                measured[key] = float(value)
    measured["magnitude_mm"] = float(vector.magnitude_mm)
    if vector.normalized_distance is None:
        reasons["normalized_distance"] = scale.code
    else:
        measured["normalized_distance"] = float(vector.normalized_distance)
    return measured, reasons


def analyze(run_dir: Path, study_uids: list[str] | None = None) -> dict[str, Any]:
    receipt_path = run_dir / "receipt.json"
    receipt = json.loads(receipt_path.read_text())
    records = receipt.get("records", []) if isinstance(receipt, dict) else []
    available = sorted(
        {
            str(row["study_uid"])
            for row in records
            if isinstance(row, dict) and row.get("study_uid")
        }
    )
    selected = sorted(set(study_uids)) if study_uids is not None else available
    studies: dict[str, Any] = {}
    per_pair: dict[tuple[str, str], list[dict[str, Any]]] = {
        (origin, target): []
        for origin in MAP_OBJECTS
        for target in MAP_OBJECTS
        if origin != target
    }
    for uid in selected:
        path = run_dir / uid / "study_map.json"
        study: dict[str, Any] = {
            "study_uid": uid,
            "path": str(path),
            "status": "unavailable",
            "positions": {},
            "missing_pairs": {},
        }
        positions: dict[str, rel.Position] = {}
        record = None
        try:
            record = unwrap_record(json.loads(path.read_text()))
        except (OSError, json.JSONDecodeError):
            pass
        if record is None:
            study["reason"] = "study_map_missing_or_invalid"
        else:
            construction_ok = record.get("construction") == "three_key_planes"
            study["construction"] = record.get("construction")
            study["knee"] = record.get("knee")
            study["scale"] = {
                "mm": _scale(record).mm,
                "source": _scale(record).source,
                "code": _scale(record).code,
            }
            objects = record.get("objects", {})
            study["status"] = "available" if construction_ok else "wrong_construction"
            if not construction_ok:
                study["reason"] = "construction_is_not_three_key_planes"
            for name in MAP_OBJECTS:
                position, details = _position_record(
                    name, objects.get(name) if isinstance(objects, dict) else None
                )
                positions[name] = position
                study["positions"][name] = details
            if construction_ok:
                scale, knee = _scale(record), record.get("knee")
                for pair, rows in per_pair.items():
                    origin, target = pair
                    a, b = positions[origin], positions[target]
                    row = {"study_uid": uid, "status": "unresolved", "reasons": {}}
                    if not a.complete:
                        row["reasons"][origin] = {
                            "status": a.status,
                            "problems": dict(a.problems),
                        }
                    if not b.complete:
                        row["reasons"][target] = {
                            "status": b.status,
                            "problems": dict(b.problems),
                        }
                    endpoints_consistent = (
                        study["positions"][origin]["construction_consistent"]
                        and study["positions"][target]["construction_consistent"]
                    )
                    if a.complete and b.complete and endpoints_consistent:
                        row["status"] = "measured"
                        row["metrics"], row["metric_reasons"] = _measure_pair(
                            a, b, scale, knee
                        )
                    elif a.complete and b.complete:
                        row["reasons"]["construction"] = (
                            "declared_position_does_not_match_key_plane_reconstruction"
                        )
                    rows.append(row)
        if record is None or not (
            isinstance(record, dict)
            and record.get("construction") == "three_key_planes"
        ):
            for rows in per_pair.values():
                rows.append(
                    {
                        "study_uid": uid,
                        "status": "unresolved",
                        "reasons": {"study": study.get("reason", "invalid_study_map")},
                    }
                )
        studies[uid] = study
    pair_rows = []
    for (origin, target), rows in per_pair.items():
        row: dict[str, Any] = {
            "origin": origin,
            "target": target,
            "coverage_studies": len(selected),
            "measured_studies": 0,
            "unresolved_studies": [],
            "metrics": {metric: [] for metric in METRICS},
        }
        for study_row in rows:
            if study_row["status"] != "measured":
                row["unresolved_studies"].append(study_row)
                continue
            row["measured_studies"] += 1
            for metric, value in study_row["metrics"].items():
                row["metrics"][metric].append(
                    {"study_uid": study_row["study_uid"], "value": value}
                )
        row["statistics"] = {
            metric: _stats([item["value"] for item in values])
            for metric, values in row["metrics"].items()
        }
        pair_rows.append(row)
    return {
        "schema": "map_pair_variation/v1",
        "source_run": str(run_dir),
        "study_count": len(selected),
        "study_uids": selected,
        "studies": studies,
        "pairs": pair_rows,
    }


def write_outputs(result: dict[str, Any], json_path: Path, table_path: Path) -> None:
    json_path.write_text(json.dumps(result, indent=2, allow_nan=False) + "\n")
    fields = [
        "origin",
        "target",
        "coverage_studies",
        "measured_studies",
        "unresolved_study_uids",
    ]
    for metric in METRICS:
        fields.extend(
            (f"{metric}_n", f"{metric}_min", f"{metric}_max", f"{metric}_sample_sd")
        )
    with table_path.open("w", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        for pair in result["pairs"]:
            row = {
                "origin": pair["origin"],
                "target": pair["target"],
                "coverage_studies": pair["coverage_studies"],
                "measured_studies": pair["measured_studies"],
                "unresolved_study_uids": json.dumps(
                    [item["study_uid"] for item in pair["unresolved_studies"]]
                ),
            }
            for metric, stats in pair["statistics"].items():
                for stat, value in stats.items():
                    row[f"{metric}_{stat}"] = value
            writer.writerow(row)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--run",
        required=True,
        type=Path,
        help="saved interiors run directory containing receipt.json",
    )
    parser.add_argument(
        "--study-uids", nargs="*", help="optional explicit study UID selection"
    )
    parser.add_argument("--out", required=True, type=Path, help="output JSON path")
    parser.add_argument("--table", required=True, type=Path, help="output CSV path")
    args = parser.parse_args(argv)
    result = analyze(args.run, args.study_uids)
    write_outputs(result, args.out, args.table)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
