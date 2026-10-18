"""Where each object's selected slices lie, in physical normalized terms (development analysis, not part of
the production run: it reads the receipts a run wrote and no image).

`.venv/bin/python scripts/slice_positions.py --run <interiors run dir> --out <table dir>` reads the run's
receipt (`objects[study]` and the records' saved `squint_centres_lps`) and writes one row per observation
(every provenance, kind, property, view; nothing reduced to a best one) with where its slice lies along the
patient axis its stack runs along.

Coordinate convention (all LPS, the scanner's millimetres, from each series' `squint_centres_lps`):

- a slice's place is the mean of its tiles' centres; the stack's direction is the mean step between consecutive
  slices; the patient axis it runs along is the LPS axis with the largest component of that direction
  (x: toward the patient's LEFT, y: toward the POSTERIOR, z: toward the HEAD);
- `q_mm` is the distance of the slice's place from the stack's lowest place along that axis (0 at the end toward
  the patient's right, the front, the feet): the order of the indices does not matter, a reversed stack gives the
  same q, and unequal spacing is carried by the actual places;
- `t` is q over the stack's extent along the axis, 0 to 1, the ends being the first and last slices' places;
- `t_side` (sagittal series only, and only where the header names the knee): 0 at the lateral end, 1 at the
  medial end. A right knee's medial side is toward the patient's left (x up), a left knee's toward the right;
- the fraction by index, slice / (n - 1), is kept beside it to show it is not the same thing.

An unknown is None, never 0: a series without finite centres, a single slice, a header naming no knee."""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

import numpy as np

AXES = ("x_toward_patient_left", "y_toward_posterior", "z_toward_head")
PLANE_AXIS = {"Sagittal": 0, "Coronal": 1, "Axial": 2}
# general context the middle slice names: no slice is claimed best for these
CONTEXT = frozenset({"air", "skin", "subcutaneous_fat", "muscle", "joint", "meniscus"})


def stack_geometry(centres: np.ndarray) -> dict:
    """The stack's places along its patient axis from the tiles' scanner-space centres
    (slices, rows, columns, 3), or why it has none: `reason`."""
    n = int(centres.shape[0])
    if n < 2:
        return {"reason": "single_slice_stack", "n": n}
    flat = centres.reshape(n, -1, 3)
    seen = np.isfinite(flat).all(axis=2)  # a tile with a centre
    total = np.where(seen[..., None], flat, 0.0).sum(axis=1)
    count = seen.sum(axis=1)[:, None]
    place = np.divide(total, count, out=np.full(total.shape, np.nan), where=count > 0)
    if not np.isfinite(place).all():
        return {"reason": "slice_without_finite_tiles", "n": n}
    step = np.diff(place, axis=0).mean(axis=0)
    norm = float(np.linalg.norm(step))
    if norm == 0:
        return {"reason": "zero_stack_step", "n": n}
    axis = int(np.argmax(np.abs(step)))
    along = place[:, axis]
    q = along - along.min()
    extent = float(q.max())
    if extent <= 0:
        return {"reason": "zero_extent", "n": n}
    gaps = np.abs(np.diff(along))
    return {
        "n": n,
        "axis": axis,
        "cosine": float(abs(step[axis]) / norm),
        "reversed": bool(step[axis] < 0),
        "q": q,
        "extent": extent,
        "mean_gap_mm": float(gaps.mean()),
        "gap_spread": float(gaps.max() / gaps.min()) if gaps.min() > 0 else None,
    }


def geometry(npz_path: Path) -> dict:
    """`stack_geometry` of a saved record's tile centres, or why the file gives none."""
    if not npz_path.exists():
        return {"reason": "artifact_missing"}
    saved = np.load(npz_path)
    if "squint_centres_lps" not in saved.files:
        return {"reason": "no_squint_centres"}
    return stack_geometry(saved["squint_centres_lps"])


def side_position(
    t: float, plane: str, knee: str | None
) -> tuple[float | None, str | None]:
    """`t` (0 toward the patient's right) as 0 lateral .. 1 medial on a sagittal series where the header
    names the knee; otherwise None and why."""
    if plane != "Sagittal":
        return None, None
    if knee == "R":  # medial is toward the patient's left
        return t, None
    if knee == "L":
        return 1.0 - t, None
    return None, "header_names_no_knee"


def role_of(o: dict) -> str:
    """How the slice came to be the one: from the observation's provenance, kind and property, and whether
    its record is the series' middle record (the file is `<series uid>.npz`) or the part's own slice's."""
    artifact = o["artifact"] or ""
    own_slice = not artifact.rsplit("/", 1)[-1].startswith(o["series_uid"] + ".npz")
    support = o["support"]
    if o["provenance"] == "projected":
        return "projected_target"
    if support.startswith("a3_posterior_trace"):
        return "continuation_trace"
    if o["kind"] == "reading":
        return "profile_run" if "profile" in support else "pointed_plane_reading"
    if o["object"] in CONTEXT:
        return "context_middle_naming"
    if "_plane_" in support or "_twin_" in support or "_laid_" in support:
        return "profile_pointed_plane"
    if own_slice:
        return "own_slice_rule"
    return "middle_bootstrap"


def observation_row(
    study: str, name: str, provenance: str, kind: str, support: str, o: dict, g: dict
) -> dict:
    """One observation as a table row with its slice's physical and normalized position."""
    o = dict(o, object=name, provenance=provenance, kind=kind)
    plane, fluid, fat = o["view"]
    slices = o["slices"]
    row = {
        "study_uid": study,
        "object": name,
        "provenance": provenance,
        "kind": kind,
        "role": role_of(o),
        "support": support,
        "series_uid": o["series_uid"],
        "plane": plane,
        "fluid_sensitive": fluid,
        "fat_suppressed": fat,
        "knee": g.get("knee"),
        "stack_slices": g.get("n"),
        "slice_first": min(slices),
        "slice_last": max(slices),
        "n_slices_in_reading": len(slices),
        "code": o["code"],
        "pixel_count": o["count"],
        "off_plane_mm": o["off_plane_mm"],
        "at_fixed_middle_index": (
            len(slices) == 1 and slices[0] == g["middle"] if "middle" in g else None
        ),
        "artifact": o["artifact"],
        "row": o["row"],
        "label": o["label"],
    }
    if "q" not in g:
        row["position_unavailable_reason"] = g.get("reason")
        return row
    qs = [float(g["q"][s]) for s in slices if 0 <= s < g["n"]]
    ts = [v / g["extent"] for v in qs]
    row.update(
        axis=AXES[g["axis"]],
        axis_matches_plane_label=PLANE_AXIS.get(plane) == g["axis"],
        stack_cosine=round(g["cosine"], 4),
        stack_reversed=g["reversed"],
        stack_extent_mm=round(g["extent"], 2),
        mean_slice_gap_mm=round(g["mean_gap_mm"], 3),
        gap_max_over_min=None if g["gap_spread"] is None else round(g["gap_spread"], 3),
        q_mm=round(float(np.mean(qs)), 2) if qs else None,
        t_patient_axis=round(float(np.mean(ts)), 4) if ts else None,
        t_first=round(ts[0], 4) if ts else None,
        t_last=round(ts[-1], 4) if ts else None,
        t_by_index=round(float(np.mean(slices)) / (g["n"] - 1), 4),
        t_side_lateral0_medial1=None,
        side_reason=None,
        offset_from_tibia_top_mm=None,
        offset_from_femur_lowest_mm=None,
    )
    if ts:
        side, why = side_position(float(np.mean(ts)), plane, g.get("knee"))
        row["t_side_lateral0_medial1"] = None if side is None else round(side, 4)
        row["side_reason"] = why
    return row


def main() -> None:
    root = Path(__file__).resolve().parent.parent
    from knee.study.corpus import open_corpus
    from knee.study.tables import labeled_uids

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--run", type=Path, required=True, help="the interiors run directory"
    )
    parser.add_argument(
        "--main-run", type=Path, required=True, help="the main-slices run directory"
    )
    parser.add_argument(
        "--out", type=Path, required=True, help="where the table is written"
    )
    parser.add_argument("--root", type=Path, default=root / "data/raw")
    args = parser.parse_args()
    labelled = list(labeled_uids(open_corpus(args.root).tables))
    inter = json.loads((args.run / "receipt.json").read_text())
    main_r = json.loads((args.main_run / "receipt.json").read_text())
    series_rec = {rec["series_uid"]: rec for rec in inter["records"]}
    geo: dict[str, dict] = {}
    for uid, rec in series_rec.items():
        g = geometry(args.run / rec["artifact"])
        g.update(
            view=tuple(rec["view"]),
            knee=rec["assignments"].get("knee"),
            middle=rec["slice_index"],
        )
        geo[uid] = g
    # the tibia's top and the femur's lowest place (z, mm), kept by a posterior trace, for axial series
    context: dict[str, list[float]] = {}
    for base, records in (
        (args.run, inter["records"]),
        (args.main_run, main_r["records"]),
    ):
        for rec in records:
            if "a3_posterior_context_up_mm" in (rec.get("arrays") or {}):
                z = np.load(base / rec["artifact"])
                context.setdefault(
                    rec["study_uid"], z["a3_posterior_context_up_mm"].tolist()
                )
    rows: list[dict] = []
    for study, objects in inter["objects"].items():
        for name, entry in objects.items():
            for provenance, kinds in entry["observations"].items():
                for kind, props in kinds.items():
                    for support, refs in props.items():
                        for o in refs:
                            g = geo.get(
                                o["series_uid"],
                                {"reason": "series_has_no_middle_record"},
                            )
                            row = observation_row(
                                study, name, provenance, kind, support, o, g
                            )
                            if (
                                row["plane"] == "Axial"
                                and "q" in g
                                and study in context
                            ):
                                top, low = context[study]
                                centres = np.load(
                                    args.run / series_rec[o["series_uid"]]["artifact"]
                                )["squint_centres_lps"]
                                z_low = float(
                                    np.nanmean(
                                        centres[..., 2].reshape(centres.shape[0], -1),
                                        axis=1,
                                    ).min()
                                )
                                z_here = z_low + float(row["q_mm"] or 0.0)
                                if row["q_mm"] is not None and np.isfinite(top):
                                    row["offset_from_tibia_top_mm"] = round(
                                        z_here - top, 2
                                    )
                                if row["q_mm"] is not None and np.isfinite(low):
                                    row["offset_from_femur_lowest_mm"] = round(
                                        z_here - low, 2
                                    )
                            rows.append(row)
    asked = [
        {
            "study_uid": rec["study_uid"],
            "object": u["object"],
            "provenance": u["provenance"],
            "series_uid": u["series_uid"],
            "view": u["view"],
            "code": u["code"],
        }
        for rec in inter["records"] + main_r["records"]
        for u in rec.get("observations_unresolved", [])
    ]
    series = [
        {
            "study_uid": rec["study_uid"],
            "series_uid": uid,
            "view": list(rec["view"]),
            "knee": rec["assignments"].get("knee"),
            "n_slices": geo[uid].get("n"),
            "geometry_reason": geo[uid].get("reason"),
        }
        for uid, rec in series_rec.items()
    ]
    args.out.mkdir(parents=True, exist_ok=True)
    table = {
        "convention": __doc__,
        "labelled_studies": labelled,
        "studies_in_receipt": sorted(inter["objects"]),
        "series": series,
        "unresolved_by_series": asked,
        "context_z_tibia_top_femur_lowest": context,
        "rows": rows,
    }
    (args.out / "observation-table.json").write_text(json.dumps(table, default=str))
    columns = list({k: None for r in rows for k in r})
    with open(args.out / "observation-table.csv", "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=columns)
        writer.writeheader()
        writer.writerows(rows)
    print(
        len(rows),
        "rows;",
        len(asked),
        "unresolved sayings;",
        len(inter["objects"]),
        "studies of",
        len(labelled),
    )


if __name__ == "__main__":
    main()
