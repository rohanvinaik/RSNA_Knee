"""Where the patella's native-resolved sections lie RELATIVE TO THE STUDY'S ANATOMICAL REFERENCE
(development analysis, not part of the production run: it reads the receipts two runs wrote and the
small arrays they saved, no image).

`.venv/bin/python scripts/reference_offsets.py --run <interiors dir> --reference-run <interiors dir>
--out <dir>` writes `reference-table` (every labelled study: the reference the production run kept
and, beside it, the one the baseline run's saved cheap profiles and native outcomes give), `offset-table`
(one row per native-resolved patella section of `--run`, with its place against the reference),
`reference-accounting` (every study and fat-suppressed sagittal series, measured or unknown with its
reason) and `reference-stats` (the offsets' count, mean, sample SD, median, quartiles and range by
kind of reference and sign convention, and a leave-one-study-out check of the central half as a
window; the studies, the series and the sections are counted apart, since a study's sections are
not independent samples).

The reference is `knee.collapse.reference`'s and `scripts/run_interiors.py::select_reference`'s: on
the first series without fat suppression (sagittal first), the slice of the strongest supported
marrow-body area of the femur or the tibia (the cheap profile, `a3_<bone>_profile_area_mm2`),
confirmed by the lens's native outcome (the middle slice is the bootstrap's own naming), the next
strongest asked where it is not. `--reference-run` is a production run that kept it live, its
support in the scanner's millimetres (`a3_reference_support_lps`); `study_reference` derives it from
the saved profiles of `--run` as a check, and where a widened plane's outcome was never saved says so
(`native_confirmation_not_saved`) rather than inventing it. A reference's place along the patella
series' own normal is the mean of its support's places along it (`reference_position`), from physical
places (the squint's tile centres of each slice), never from slice indices. An offset is made positive
medially (a sagittal series whose header names the knee) or toward the patient's left. An unknown is
None with its reason, never 0. No diagnosis label is read."""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

import numpy as np

from knee.array_archive import open_arrays
from knee.collapse.bones import IDENTIFIED, OUTCOMES
from knee.collapse.reference import (
    REFERENCE_BONES,
    REFERENCE_VIEWS,
    offset_sign,
    reference_position,
    strongest_first,
)
from knee.json_store import load_json


def places(saved) -> np.ndarray:
    """Each slice's place, the mean of its squint tiles' centres (Z, 3): NaN where none is seen."""
    centres = np.asarray(saved["squint_centres_lps"], dtype=float)
    flat = centres.reshape(centres.shape[0], -1, 3)
    out = np.full((len(flat), 3), np.nan)
    for z, tiles in enumerate(flat):
        seen = tiles[np.isfinite(tiles).all(axis=1)]
        if len(seen):
            out[z] = seen.mean(axis=0)
    return out


def normal_of(slice_places: np.ndarray) -> np.ndarray | None:
    """The unit direction the stack runs in, first to last slice; None for fewer than two places."""
    seen = np.flatnonzero(np.isfinite(slice_places).all(axis=1))
    if len(seen) < 2:
        return None
    step = slice_places[seen[-1]] - slice_places[seen[0]]
    length = float(np.linalg.norm(step))
    return step / length if length > 0 else None


def saved_code(saved, record: dict, bone: str, z: int) -> str:
    """The native outcome the run saved for slice z of a series for a bone: the bootstrap's naming
    on the middle slice, the pointed plane's outcome elsewhere, or that none was saved."""
    if z == record["slice_index"]:
        return IDENTIFIED if record["assignments"].get(bone) is not None else "unnamed"
    slices = saved.get(f"a3_{bone}_plane_slices") if hasattr(saved, "get") else None
    names = f"a3_{bone}_plane_slices"
    if names not in saved.files:
        return "native_confirmation_not_saved"
    slices = list(saved[names])
    outcome = saved[f"a3_{bone}_plane_outcome"]
    if z not in slices:
        return "native_confirmation_not_saved"
    code = int(outcome[slices.index(z)])
    return OUTCOMES[code] if 0 <= code < len(OUTCOMES) else "unreadable_geometry"


def study_reference(records: list[dict], saved_of) -> dict:
    """One study's reference from its saved cheap profiles and native outcomes, by the production
    rule: series in the order of `REFERENCE_VIEWS` that did not suppress fat; within one, the bones'
    strongest groups of equal area, strongest first, until one holds a confirmed slice."""
    order = [
        r
        for view in REFERENCE_VIEWS
        for r in records
        if r["view"][0] == view and r["view"][2] == "0"
    ]
    tried: list[dict] = []
    for record in order:
        saved = saved_of(record)
        groups = []
        for bone in REFERENCE_BONES:
            name = f"a3_{bone}_profile_area_mm2"
            if name not in saved.files:
                tried.append(
                    {
                        "series_uid": record["series_uid"],
                        "bone": bone,
                        "why": record["bones"]["codes"].get(bone, "no_bone_record"),
                    }
                )
                continue
            for tier, group in strongest_first(saved[name]):
                groups.append((tier, float(saved[name][group[0]]), bone, group))
        for _tier, area, bone, group in sorted(groups, key=lambda g: (g[0], -g[1])):
            codes = {z: saved_code(saved, record, bone, z) for z in group}
            tried.append(
                {
                    "series_uid": record["series_uid"],
                    "bone": bone,
                    "slices": list(group),
                    "area_mm2": area,
                    "codes": {str(z): c for z, c in codes.items()},
                }
            )
            confirmed = [z for z, c in codes.items() if c == IDENTIFIED]
            if confirmed:
                return {
                    "series_uid": record["series_uid"],
                    "view": record["view"],
                    "bone": bone,
                    "slices": confirmed,
                    "tied": len(group) > 1,
                    "area_mm2": area,
                    "knee": record["assignments"].get("knee"),
                    "asked": tried,
                    "code": "reference_confirmed",
                }
    return {"code": "no_confirmed_key_plane", "asked": tried}


def describe(values: list[float]) -> dict:
    """Count, mean, SAMPLE SD (None for fewer than two), median, quartiles and range."""
    v = np.asarray([x for x in values if x is not None and math.isfinite(x)], float)
    if not len(v):
        return {"n": 0}
    q1, med, q3 = np.percentile(v, [25, 50, 75])
    return {
        "n": len(v),
        "mean": float(v.mean()),
        "sd": float(v.std(ddof=1)) if len(v) > 1 else None,
        "median": float(med),
        "q1": float(q1),
        "q3": float(q3),
        "min": float(v.min()),
        "max": float(v.max()),
    }


def live_reference(records: list[dict], saved_of) -> dict | None:
    """The reference the production run kept for one study (`record["reference"]` and its saved
    support), or None where it kept none."""
    for record in records:
        kept = record.get("reference") or {}
        if kept.get("code") == "reference_confirmed":
            saved = saved_of(record)
            bone = kept["bone"]
            thick = kept.get("thickness_mm")
            if thick is None:
                thick = float(
                    saved[f"a3_{bone}_slice_thickness_mm"][min(kept["slices"])]
                )
            return {
                **kept,
                "record": record,
                "support": saved["a3_reference_support_lps"],
                "thickness_mm": thick,
            }
    return None


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--run",
        type=Path,
        required=True,
        help="the run whose patella sections are measured",
    )
    parser.add_argument(
        "--reference-run",
        type=Path,
        required=True,
        help="a production run that kept each study's reference (`select_reference`)",
    )
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    runs = {}
    for name, path in (("obs", args.run), ("ref", args.reference_run)):
        receipt = load_json(path / "receipt.json")
        by_study: dict[str, list[dict]] = {}
        for record in receipt["records"]:
            by_study.setdefault(record["study_uid"], []).append(record)
        runs[name] = (path, by_study)
    cache: dict[tuple[str, str], object] = {}

    def saved_in(which: str):
        def load(record: dict):
            key = (which, record["artifact"])
            if key not in cache:
                cache[key] = open_arrays(
                    runs[which][0] / record["artifact"], allow_pickle=False
                )
            return cache[key]

        return load

    try:
        _reference_offsets(args, runs, saved_in, cache)
    finally:
        for archive in cache.values():
            archive.close()


def _reference_offsets(args, runs, saved_in, cache) -> None:
    references, offsets, accounting, slice_rows = [], [], [], []
    agreement = {"same": 0, "different": 0, "saved_profiles_unconfirmed": 0}
    for study, records in sorted(runs["obs"][1].items()):
        ref_records = runs["ref"][1].get(study, [])
        live = live_reference(ref_records, saved_in("ref"))
        saved_ref = study_reference(records, saved_in("obs"))
        if saved_ref["code"] != "reference_confirmed":
            agreement["saved_profiles_unconfirmed"] += 1
        elif live is not None and (
            saved_ref["series_uid"],
            saved_ref["bone"],
            saved_ref["slices"],
        ) == (live["series_uid"], live["bone"], live["slices"]):
            agreement["same"] += 1
        else:
            agreement["different"] += 1
        references.append(
            {
                "study_uid": study,
                "live": None
                if live is None
                else {k: v for k, v in live.items() if k not in ("record", "support")},
                "from_the_saved_profiles": saved_ref,
            }
        )
        status = {
            "study_uid": study,
            "reference": "reference_confirmed" if live else "no_reference",
            "series": [],
        }
        if live is None:
            status["unknown"] = "no_confirmed_key_plane_or_no_series_to_read_it_on"
            accounting.append(status)
            for archive in cache.values():
                archive.close()
            cache.clear()
            continue
        for record in (r for r in records if r["view"] == ["Sagittal", "1", "1"]):
            saved = saved_in("obs")(record)
            target_places = places(saved)
            target_normal = normal_of(target_places)
            row = {"series_uid": record["series_uid"], "sections": 0}
            native = [
                o
                for o in record["observations"]
                if o["object"] == "patella"
                and o["provenance"] == "native"
                and o["kind"] == "resolved"
            ]
            knee = str(record["assignments"].get("knee") or "")
            left = (
                None
                if target_normal is None
                else offset_sign(target_normal, "Coronal", "")
            )
            position = (
                None
                if target_normal is None
                else reference_position(
                    live["support"], target_normal, live["thickness_mm"]
                )
            )
            if left is None or position is None:
                row["unknown"] = "no_physical_places_of_the_slices"
            elif not native:
                row["unknown"] = "no_native_resolved_patella_section"
            else:
                mean, _, _, kind = position
                assert target_normal is not None
                sided = offset_sign(target_normal, "Sagittal", knee)
                medial = (
                    sided[0] if sided is not None and sided[1] == "medial" else None
                )
                along = target_places @ target_normal - mean
                biggest = max(native, key=lambda o: o["count"] or 0)
                for o in native:
                    here = float(along[o["slices"][0]])
                    offsets.append(
                        {
                            "study_uid": study,
                            "series_uid": record["series_uid"],
                            "slice": o["slices"][0],
                            "pixels": o["count"],
                            "representative": o is biggest,
                            "knee": knee or None,
                            "reference_series_uid": live["series_uid"],
                            "reference_bone": live["bone"],
                            "reference_slices": live["slices"],
                            "kind": kind,
                            "left_mm": left[0] * here,
                            "medial_mm": None if medial is None else medial * here,
                        }
                    )
                    row["sections"] += 1
                # where every slice of the series lies against the reference, to ask of a window
                # how much of the stack it covers
                slice_rows.append(
                    {
                        "study_uid": study,
                        "series_uid": record["series_uid"],
                        "kind": kind,
                        "left_mm": [float(left[0] * v) for v in along],
                        "medial_mm": None
                        if medial is None
                        else [float(medial * v) for v in along],
                    }
                )
            status["series"].append(row)
        accounting.append(status)
        for archive in cache.values():
            archive.close()
        cache.clear()
    stats: dict = {"reference_agreement_live_vs_saved_profiles": agreement}
    for kind in ("depth", "in_plane"):
        for convention in ("left_mm", "medial_mm"):
            for scope, rows in (
                ("sections", [o for o in offsets if o["kind"] == kind]),
                (
                    "representatives",
                    [o for o in offsets if o["kind"] == kind and o["representative"]],
                ),
            ):
                key = f"{kind}:{convention}:{scope}"
                values = [o[convention] for o in rows]
                stats[key] = describe(values)
                stats[key]["series"] = len(
                    {o["series_uid"] for o in rows if o[convention] is not None}
                )
                stats[key]["studies"] = len(
                    {o["study_uid"] for o in rows if o[convention] is not None}
                )
            stats[f"{kind}:{convention}:window_leave_one_study_out"] = window_check(
                [o for o in offsets if o["kind"] == kind],
                [r for r in slice_rows if r["kind"] == kind],
                convention,
            )
    args.out.mkdir(parents=True, exist_ok=True)
    (args.out / "reference-table.json").write_text(json.dumps(references, indent=1))
    (args.out / "offset-table.json").write_text(json.dumps(offsets, indent=1))
    (args.out / "reference-accounting.json").write_text(
        json.dumps(accounting, indent=1)
    )
    (args.out / "reference-stats.json").write_text(json.dumps(stats, indent=1))
    print(json.dumps(stats, indent=1))
    confirmed = sum(1 for r in references if r["live"] is not None)
    print(
        len(references),
        "studies;",
        confirmed,
        "with a reference;",
        len(offsets),
        "sections",
    )


def window_check(offsets: list[dict], slice_rows: list[dict], convention: str) -> dict:
    """For each series with a representative, the central half (quartiles) of the OTHER studies'
    representatives' offsets as its window: whether its own representative lies in it and what
    share of its slices the window covers. A pointer's hit rate and size, measured out of sample."""
    reps = [o for o in offsets if o["representative"] and o[convention] is not None]
    hits = covered = total = 0
    shares: list[float] = []
    for rep in reps:
        others = [o[convention] for o in reps if o["study_uid"] != rep["study_uid"]]
        if len(others) < 2:
            continue
        low, high = np.percentile(others, [25, 75])
        hits += int(bool(low <= rep[convention] <= high))
        slices = next(
            r[convention] for r in slice_rows if r["series_uid"] == rep["series_uid"]
        )
        inside = [bool(low <= v <= high) for v in slices]
        shares.append(sum(inside) / len(inside))
        covered += sum(inside)
        total += len(inside)
    return {
        "representatives": len(reps),
        "hit_in_the_window": hits,
        "mean_share_of_slices_in_the_window": float(np.mean(shares))
        if shares
        else None,
        "slices_in_the_window": covered,
        "slices": total,
    }


if __name__ == "__main__":
    main()
