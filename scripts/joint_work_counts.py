"""The joint family's measured work and what it named, one run against another (development
analysis; reads two receipts, no image).

`.venv/bin/python scripts/joint_work_counts.py --before <interiors dir> --after <interiors dir> --out
<file>` sums the two runs' ledgers over the studies both hold (the joint family's cheap profile
readings, planes asked, window counters, and the run's lens, field, cheap-profile and fields-made
totals) and lists, per series, how the joint family's native observations differ: the planes read, the
objects each named, and every object/kind/slice present in one and not the other. A difference is
reported, never judged: a plane the new search did not ask is a pointer, not an absence."""

from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path

from knee.json_store import load_json

JOINT_OBJECTS = {
    "medial_meniscus",
    "lateral_meniscus",
    "meniscus",
    "femoral_cartilage",
    "tibial_cartilage",
    "mcl",
    "pcl",
    "acl",
}


def load(path: Path) -> tuple[dict, dict]:
    receipt = load_json(path / "receipt.json")
    return {r["series_uid"]: r for r in receipt["records"]}, receipt["telemetry"]


def totals(telemetry: dict, studies: set[str]) -> Counter:
    out: Counter = Counter()
    for study in studies:
        events = telemetry[study]["events"]
        for name, counts in events.items():
            if (
                name.startswith(
                    ("joint.", "patella.", "reference.", "bones.", "recess.")
                )
                or name in ("lens.made", "field.made", "lens.handed_on")
                or name.endswith((".cheap_readings", ".lens_readings"))
            ):
                for key, value in counts.items():
                    out[f"{name}:{key}"] += value
    return out


def native_joint(record: dict) -> set[tuple]:
    return {
        (o["object"], o["kind"], o["support"], tuple(o["slices"]))
        for o in record.get("observations", [])
        if o["provenance"] == "native" and o["object"] in JOINT_OBJECTS
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--before", type=Path, required=True)
    parser.add_argument("--after", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    before, tb = load(args.before)
    after, ta = load(args.after)
    studies = set(tb) & set(ta)
    series = sorted(
        s for s in set(before) & set(after) if before[s]["study_uid"] in studies
    )
    rows = []
    for uid in series:
        b, a = before[uid], after[uid]
        jb, ja = b.get("joint") or {}, a.get("joint") or {}
        gone, new = native_joint(b) - native_joint(a), native_joint(a) - native_joint(b)
        rows.append(
            {
                "series_uid": uid,
                "study_uid": b["study_uid"],
                "view": b["view"],
                "planes_before": [
                    p["slice"] for p in jb.get("pointed_planes", []) if not p["middle"]
                ],
                "planes_after": [
                    p["slice"] for p in ja.get("pointed_planes", []) if not p["middle"]
                ],
                "native_joint_only_before": sorted(map(list, gone)),
                "native_joint_only_after": sorted(map(list, new)),
                "stopped": (ja.get("search") or {}).get("stopped"),
                "search_code": (ja.get("search") or {}).get("code"),
            }
        )
    tot_b, tot_a = totals(tb, studies), totals(ta, studies)
    keys = sorted(set(tot_b) | set(tot_a))
    payload = {
        "studies": len(studies),
        "series": len(series),
        "ledger": {k: {"before": tot_b[k], "after": tot_a[k]} for k in keys},
        "series_differences": rows,
        "series_with_changed_native_joint_observations": sum(
            1
            for r in rows
            if r["native_joint_only_before"] or r["native_joint_only_after"]
        ),
        "series_with_a_plane_not_asked_now": sum(
            1 for r in rows if set(r["planes_before"]) - set(r["planes_after"])
        ),
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(payload, indent=1))
    for k in keys:
        if k.startswith(("joint.", "lens.made")):
            print(k, tot_b[k], "->", tot_a[k])
    print(
        payload["series"],
        "series;",
        payload["series_with_changed_native_joint_observations"],
        "with changed native joint observations;",
        payload["series_with_a_plane_not_asked_now"],
        "with a plane not asked now",
    )


if __name__ == "__main__":
    main()
