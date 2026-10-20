"""Where the joint family's observations lie RELATIVE TO THE STUDY'S ANATOMICAL REFERENCE
(development analysis, not part of the production run: it reads the receipts two runs wrote and the
small arrays they saved, no image).

`.venv/bin/python scripts/joint_reference_offsets.py --run <baseline interiors dir> --reference-run
<interiors dir that kept each study's reference> --out <dir>` writes `joint-offset-table` (one row per
observation of a joint-family object on a series of `--run`, with its place against the reference in
every physical convention the series' axis supports), `joint-offset-stats` (count, mean, sample SD,
median, quartiles and range by object, view and sequence, ROLE, kind of reference and convention;
studies, series and sections counted apart) and `joint-window-check` (the leave-one-study-out check of
the central half as a window, for each population wired).

Roles are kept apart and never pooled: `bootstrap` (the middle slice's own naming, a fixed place the
run read first, never evidence of where a part is best seen), `own_slice` (the ACL's or the LCL's own
main slice), `profile_resolved` (a pointed plane where the existing rule named the part AND the bones'
family natively identified both bones there), `profile_reading` (the rule's decision where the bones
were not established there, or the sagittal horn / cartilage candidates its gate refuses), and
`cruciate_reading` (the PCL / ACL on an additional plane). Laid and projected rows are no observation
of a place and are never used. Positions are the scanner's millimetres along the target series' own
normal (the squint's tile centres, never slice indices), minus the reference's place along it
(`reference_position`), signed by a physical direction (`offset_direction`). The baseline run's
observations are independent of the reference run: nothing is calibrated from a search that this
window itself limited."""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

import numpy as np

from knee.array_archive import open_arrays
from knee.collapse.profile import positive_runs, run_maxima
from knee.collapse.reference import (
    offset_direction,
    reference_position,
)
from knee.json_store import load_json
from scripts.reference_offsets import describe, live_reference, normal_of, places

JOINT_OBJECTS = (
    "medial_meniscus",
    "lateral_meniscus",
    "meniscus",
    "femoral_cartilage",
    "tibial_cartilage",
    "mcl",
    "pcl",
    "acl",
)


def role_of(o: dict, record: dict) -> str | None:
    """Which kind of place an observation row is, or None for laid and projected rows (not a
    reading of where the part lies)."""
    if o["provenance"] != "native":
        return None
    if o["support"] == "a3_joint_plane_objects":
        if o["object"] in ("pcl", "acl"):
            return "cruciate_reading"
        return "profile_resolved" if o["kind"] == "resolved" else "profile_reading"
    if o["support"] == "a3_joint_plane_reading":
        return "profile_reading"
    if o["support"] == "a1_objects":
        own = o.get("artifact") == record["artifact"] and o["slices"] == [
            record["slice_index"]
        ]
        return "bootstrap" if own else "own_slice"
    return None


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run", type=Path, required=True)
    parser.add_argument("--reference-run", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    receipts = {}
    for name, path in (("obs", args.run), ("ref", args.reference_run)):
        records = load_json(path / "receipt.json")["records"]
        by_study: dict[str, list[dict]] = {}
        for record in records:
            by_study.setdefault(record["study_uid"], []).append(record)
        receipts[name] = (path, by_study)
    cache: dict[tuple[str, str], object] = {}

    def saved_in(which: str):
        def load(record: dict):
            key = (which, record["artifact"])
            if key not in cache:
                cache[key] = open_arrays(
                    receipts[which][0] / record["artifact"], allow_pickle=False
                )
            return cache[key]

        return load

    try:
        _joint_offsets(args, receipts, saved_in)
    finally:
        for archive in cache.values():
            archive.close()


def _joint_offsets(args, receipts, saved_in) -> None:
    rows: list[dict] = []
    seen_series = 0
    for study, records in sorted(receipts["obs"][1].items()):
        live = live_reference(receipts["ref"][1].get(study, []), saved_in("ref"))
        if live is None:
            continue
        for record in records:
            if record["view"][0] not in ("Sagittal", "Coronal"):
                continue
            joint = record.get("joint") or {}
            if "pointed_planes" not in joint and not record.get("observations"):
                continue
            saved = saved_in("obs")(record)
            where = places(saved)
            normal = normal_of(where)
            if normal is None:
                continue
            knee = str(record["assignments"].get("knee") or "")
            direction = offset_direction(normal, record["view"][0], knee)
            position = reference_position(live["support"], normal, live["thickness_mm"])
            if direction is None or position is None:
                continue
            seen_series += 1
            mean, low, high, kind = position
            along = where @ normal
            for o in record["observations"]:
                if o["object"] not in JOINT_OBJECTS:
                    continue
                role = role_of(o, record)
                if role is None:
                    continue
                for z in o["slices"]:
                    if not (0 <= z < len(along) and math.isfinite(along[z])):
                        continue
                    rows.append(
                        {
                            "study_uid": study,
                            "series_uid": record["series_uid"],
                            "object": o["object"],
                            "view": record["view"],
                            "role": role,
                            "kind_of_observation": o["kind"],
                            "code": o.get("code"),
                            "support": o.get("support"),
                            "row": o.get("row"),
                            "slice": z,
                            "pixels": o.get("count"),
                            "reference_kind": kind,
                            "reference_view": live["view"],
                            "reference_bone": live["bone"],
                            "convention": direction[1],
                            "offset_mm": float(direction[0] * (along[z] - mean)),
                            # where in the span the reference's own support covers along this
                            # axis (0 at its low edge, 1 at its high), only for a landmark in plane
                            "across_support": None
                            if kind == "depth" or high <= low
                            else float(
                                (direction[0] * (along[z] - low) / (high - low))
                                if direction[0] > 0
                                else (high - along[z]) / (high - low)
                            ),
                            "knee": knee or None,
                        }
                    )
    pointers, series_rows = pointer_rows(receipts, saved_in)
    # the representative of a population: its largest section per series and object
    best: dict[tuple, dict] = {}
    for row in rows:
        key = (row["series_uid"], row["object"], row["role"])
        if key not in best or (row["pixels"] or 0) > (best[key]["pixels"] or 0):
            best[key] = row
    stats: dict[str, dict] = {}
    groups = sorted(
        {
            (
                r["object"],
                "/".join(r["view"]),
                r["role"],
                r["kind_of_observation"],
                r["reference_kind"],
                r["convention"],
            )
            for r in rows
        }
    )
    for obj, view, role, kind_obs, ref_kind, convention in groups:
        for scope, data in (
            ("representatives", list(best.values())),
            ("sections", rows),
        ):
            chosen = [
                r
                for r in data
                if (r["object"], "/".join(r["view"]), r["role"]) == (obj, view, role)
                and r["kind_of_observation"] == kind_obs
                and r["reference_kind"] == ref_kind
                and r["convention"] == convention
            ]
            entry = describe([r["offset_mm"] for r in chosen])
            entry["series"] = len({r["series_uid"] for r in chosen})
            entry["studies"] = len({r["study_uid"] for r in chosen})
            stats[f"{obj}|{view}|{role}|{kind_obs}|{ref_kind}|{convention}|{scope}"] = (
                entry
            )
    pointer_stats = pointer_statistics(pointers, series_rows)
    args.out.mkdir(parents=True, exist_ok=True)
    (args.out / "joint-pointer-table.json").write_text(json.dumps(pointers, indent=1))
    (args.out / "joint-pointer-stats.json").write_text(
        json.dumps(pointer_stats, indent=1)
    )
    (args.out / "joint-offset-table.json").write_text(json.dumps(rows, indent=1))
    (args.out / "joint-offset-stats.json").write_text(json.dumps(stats, indent=1))
    print(len(rows), "rows;", seen_series, "series with a reference and a place")


def pointer_rows(receipts: dict, saved_in) -> tuple[list[dict], list[dict]]:
    """The CANDIDATE population: where each quantity's cheap profile pointed (the strongest run's
    maximum other than the middle slice, ties kept) in the baseline run, against the reference, with
    every slice the baseline read (`series_rows`, for the share of a window's slices). Candidate
    pointers, never names: kept apart from the native-resolved rows."""
    pointers: list[dict] = []
    series_rows: list[dict] = []
    for study, records in sorted(receipts["obs"][1].items()):
        live = live_reference(receipts["ref"][1].get(study, []), saved_in("ref"))
        if live is None:
            continue
        for record in records:
            joint = record.get("joint") or {}
            if "pointed_planes" not in joint or record["view"][0] not in (
                "Sagittal",
                "Coronal",
            ):
                continue
            saved = saved_in("obs")(record)
            where = places(saved)
            normal = normal_of(where)
            if normal is None:
                continue
            knee = str(record["assignments"].get("knee") or "")
            direction = offset_direction(normal, record["view"][0], knee)
            position = reference_position(live["support"], normal, live["thickness_mm"])
            if direction is None or position is None:
                continue
            mean, _, _, kind = position
            along = direction[0] * (where @ normal - mean)
            for q in joint["quantities"]:
                area = np.asarray(saved[f"a3_joint_{q}_area_mm2"], dtype=float)
                status = np.asarray(saved[f"a3_joint_{q}_status"])
                read = status != 0  # every slice the baseline read (not "not read")
                series_rows.append(
                    {
                        "series_uid": record["series_uid"],
                        "study_uid": study,
                        "quantity": q,
                        "view": record["view"],
                        "reference_kind": kind,
                        "reference_bone": live["bone"],
                        "convention": direction[1],
                        "read_offsets_mm": [
                            float(v) for v in along[read & np.isfinite(along)]
                        ],
                    }
                )
                runs = positive_runs(area)
                held = [
                    int(z)
                    for peaks in run_maxima(area, runs)
                    for z in peaks
                    if z != record["slice_index"]
                ]
                if not held:
                    continue
                top = max(float(area[z]) for z in held)
                for z in [z for z in held if float(area[z]) == top]:
                    if np.isfinite(along[z]):
                        pointers.append(
                            {
                                "study_uid": study,
                                "series_uid": record["series_uid"],
                                "quantity": q,
                                "view": record["view"],
                                "slice": z,
                                "area_mm2": top,
                                "reference_kind": kind,
                                "reference_bone": live["bone"],
                                "convention": direction[1],
                                "offset_mm": float(along[z]),
                            }
                        )
    return pointers, series_rows


def pointer_statistics(pointers: list[dict], series_rows: list[dict]) -> dict:
    """Per quantity, view (plane / fat suppression), kind of reference and convention: the offsets'
    description (series and studies counted apart), and a leave-one-study-out check of the central
    half as a window: how often it holds a series' pointed representative and what share of the
    slices the baseline read lie in it."""
    stats: dict[str, dict] = {}

    def key_of(p: dict) -> tuple:
        return (
            p["quantity"],
            p["view"][0],
            p["view"][2],
            p["reference_kind"],
            p["convention"],
            p["reference_bone"],
        )

    for q, plane, fs, kind, convention, bone in sorted({key_of(p) for p in pointers}):
        mine = [
            p for p in pointers if key_of(p) == (q, plane, fs, kind, convention, bone)
        ]
        reps: dict[str, dict] = {}
        for p in mine:
            reps.setdefault(p["series_uid"], p)
        entry = describe([p["offset_mm"] for p in reps.values()])
        entry["series"] = len(reps)
        entry["studies"] = len({p["study_uid"] for p in reps.values()})
        hits = tested = 0
        covered = total = 0
        for rep in reps.values():
            others = [
                p["offset_mm"]
                for p in reps.values()
                if p["study_uid"] != rep["study_uid"]
            ]
            if len(others) < 2:
                continue
            low, high = np.percentile(others, [25, 75])
            tested += 1
            hits += int(low <= rep["offset_mm"] <= high)
            read = next(
                r["read_offsets_mm"]
                for r in series_rows
                if r["series_uid"] == rep["series_uid"] and r["quantity"] == q
            )
            covered += sum(1 for v in read if low <= v <= high)
            total += len(read)
        entry["leave_one_study_out"] = {
            "tested": tested,
            "held_in_the_central_half": hits,
            "read_slices_in_it": covered,
            "read_slices": total,
        }
        stats[f"{q}|{plane}/{fs}|{kind}|{convention}|{bone}"] = entry
    return stats


if __name__ == "__main__":
    main()
