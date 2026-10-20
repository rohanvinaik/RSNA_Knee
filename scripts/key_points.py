"""Each object's reference position from its THREE KEY PLANES, in the leg's physical space (development tool for
the relative position map, `docs/RELATIVE_POSITION_MAP.md` §0 and §8.8; never part of the production run).

Rohan, 2026-10-17: «The "key slice" is just the one slice, seperately for each of the 3 different views [...]
where the anatomy is most obvious» · «Obects are resolved in 3D with vector distances in magnitude and direction».
An object's key plane in each of sagittal, coronal and axial is a SELECTED slice of one acquisition; the three
planes' actual normals and offsets are solved together (N p = d, `knee.collapse.relative.reference_position`) for
the object's reference position. Each coordinate's authority is its view's key plane. Nothing here takes a
centroid, averages sections, or promotes the largest section to a key slice. The object's whole shape and support
stay in its observations.

Output (`construction = "three_key_planes"`, `schema = "three_key_planes/v1"`): per study and object, the
`status` (`complete`, or `partial` / `singular_planes` / ... with the constraints known and no point), the
`position_lps` (scanner millimetres, x toward the patient's left, y toward the back, z toward the head) only when
complete, the actual source plane per orientation (series, native slice, normal, offset, precision, reason,
provenance, the header's plane word, and the native section saved at that slice if the run resolved one), and
`problems`: each orientation without a usable plane and its own code (`not_supplied` is unknown, never an
absence; `refused`, `tied`, `absent_in_view`, `repeated_orientation`, `invalid:*` are each their own). The old
centroid schema is gone: `key_point`, `lps` and `depth_axis` do not exist in this output, and a table written by
the withdrawn construction is not three-plane map data.

Inventory kept as DIAGNOSTIC only (`key_sections`, `sections`): every natively resolved section of every part from
the run's receipts, with its source address, pixel count, area, its extent, the slice's normal and offset, and its
`diagnostic_centroid_lps`. The largest section per series is listed so the planes the caller selects can be
checked against what the run resolved there; it is not a key plane and no position reads it.

Which slice is each object's key plane in each orientation is the CALLER's selection (`--key-planes`; the cheap
per-object selection is the parent's). Without it every orientation is `not_supplied` and no object has a point.

`.venv/bin/python scripts/key_points.py --run <interiors dir> --main-run <main dir> --out <table.json>
    [--key-planes <key_planes.json>] [--knee-scale <scales.json>] [--pairs]
    [--study-uid <uid> ...] [--draw <study uid> ... --pictures <dir>]`

`--key-planes` file: {"schema": "key_planes/v1", "studies": {<study uid>: {<object>: {<orientation>: <entry>}}}}.
An entry (or a list of entries, which is a repeated orientation and stays unresolved) is
{"outcome": "selected" (default) | "refused" | "tied" | "absent_in_view", "series_uid", "slice", "reason",
"provenance", "candidates": [{"series_uid", "slice"}] (a tie), "precision_mm"}; a selected plane's geometry is the
actual slice's header frame, unless the entry gives its own "normal" with "origin_lps" or "offset_mm". An
orientation the entry names must agree with the series' own plane word.
`--knee-scale` file: {<study uid>: {"mm": <positive millimetres>, "source": <text>}}; without it the scale is
`scale_unknown` and nothing is normalized.
`--draw` (development only; matplotlib is imported only here) draws, per object, each source plane's actual image
with the other planes' traces, the object's section where the run resolved one, the point, and the point carried
onto every other series' nearest slice.
"""

from __future__ import annotations

import argparse
import json
import math
from collections import defaultdict
from pathlib import Path

import numpy as np

from knee.array_archive import open_arrays
from knee.collapse import relative as rel
from knee.collapse.physical import PlaneFrame
from knee.json_store import load_json
from knee.study.corpus import KAGGLE_ROOT, LOCAL_ROOT, open_corpus, read_study

ROOT = Path(__file__).resolve().parent.parent
SCHEMA = "three_key_planes/v1"
CONSTRUCTION = "three_key_planes"
KEY_PLANES_SCHEMA = "key_planes/v1"

# Which family's cheap profile points the planes a part is resolved on, and the record part that lists them.
# (Information about how a section's slice was found; it never says which section is a key plane.)
FAMILY = {
    "femur": ("bones", "femur"),
    "tibia": ("bones", "tibia"),
    "patella": ("patella", None),
    "hoffa_fat_pad": ("patella", None),
    "suprapatellar_fat": ("patella", None),
    "quadriceps_fat_pad": ("patella", None),
    "prefemoral_fat_pad": ("patella", None),
    "patellar_tendon": ("patella", None),
    "quadriceps_tendon": ("patella", None),
    "medial_meniscus": ("joint", None),
    "lateral_meniscus": ("joint", None),
    "meniscus": ("joint", None),
    "femoral_cartilage": ("joint", None),
    "tibial_cartilage": ("joint", None),
    "mcl": ("joint", None),
    "pcl": ("joint", None),
    "acl": ("joint", None),
    "joint_fluid": ("recess", None),
    "anterior_synovial_recess": ("recess", None),
    "synovium": ("recess", None),
    "joint_capsule": ("recess", None),
    "medial_patellar_retinaculum": ("recess", None),
    "lateral_patellar_retinaculum": ("recess", None),
    "fibula": ("fibula", None),
}
# Parts that are not one compact body. Informational only: the caller's selected planes decide whether a
# position exists; a distributed part's sections are kept and the flag travels with its record.
DISTRIBUTED = frozenset(
    {"air", "skin", "subcutaneous_fat", "muscle", "joint", "meniscus", "joint_fluid"}
)
PROFILE_SUPPORTS = (
    "a3_femur_plane",
    "a3_tibia_plane",
    "a3_patella_plane",
    "a3_joint_plane",
    "a3_recess_plane",
    "a3_fibula_detailed",
)
SECTION_KEYS = (
    "view",
    "slice",
    "selection",
    "support",
    "row",
    "pixels",
    "area_mm2",
    "diagnostic_centroid_lps",
    "plane_offset_mm",
    "normal_lps",
    "half_spacing_mm",
)


def frame_of(series, z: int) -> PlaneFrame | None:
    geometry = series.geometry
    if geometry is None:
        return None
    try:
        return PlaneFrame.from_dicom(
            geometry.position[z], geometry.orientation[z], geometry.spacing[z]
        )
    except ValueError:
        return None


def half_step_mm(frames: list[PlaneFrame | None], z: int) -> float:
    """How finely a slice's own place is known: half the step to its neighbour along its normal (the next slice,
    else the previous); NaN where it has none or no frame."""
    frame = frames[z]
    if frame is None:
        return math.nan
    normal = np.asarray(frame.normal(), dtype=float)
    for j in (z + 1, z - 1):
        neighbour = frames[j] if 0 <= j < len(frames) else None
        if neighbour is not None:
            origin = np.asarray(neighbour.origin_lps) - np.asarray(frame.origin_lps)
            return abs(float(origin @ normal)) / 2.0
    return math.nan


def series_frames(series) -> dict:
    """One series' per-slice frames (None where the header gives none), its image shape and the header's plane
    word: what places a point in it."""
    n = len(series.slices)
    frames = [frame_of(series, z) for z in range(n)] if n else []
    if series.volume is not None:
        shape = tuple(int(v) for v in series.volume.shape[1:])
    elif n:
        shape = tuple(int(v) for v in series.slices[0].pixels.shape)
    else:
        shape = None
    return {
        "frames": frames,
        "shape": shape,
        "plane": str(getattr(series.row, "anatomical_plane", "")),
    }


def middle_pointed(record: dict, name: str) -> bool:
    """Whether the part's family's cheap profile pointed to the series' middle slice."""
    family, key = FAMILY.get(name, (None, None))
    part = record.get(family) if family else None
    if isinstance(part, dict) and key is not None:
        part = part.get(key)
    if not isinstance(part, dict):
        return False
    return any(p.get("middle") for p in part.get("pointed_planes", []))


def selection_of(o: dict, record: dict, own_slice: bool) -> str:
    """How the run came to resolve this section on this slice (information only)."""
    support = o["support"]
    if support.startswith(PROFILE_SUPPORTS):
        return f"{FAMILY.get(o['object'], ('profile',))[0]}_profile"
    if own_slice and o["object"] == "fibula":
        return "fibula_profile"
    if own_slice:
        return "own_slice_rule"
    if middle_pointed(record, o["object"]):
        return f"{FAMILY[o['object']][0]}_profile_at_the_middle"
    return "middle_bootstrap"


def sections_of(
    run: Path, main_run: Path, root: Path, studies: set[str] | None
) -> tuple[list[dict], dict, dict]:
    """Every natively resolved section of every part (the inventory, with its source address and provenance), per
    study the series' summary, and per study the series' frames. Centroids here are DIAGNOSTIC."""
    rows: list[dict] = []
    geometry: dict[str, dict] = {}
    frames: dict[str, dict] = {}
    receipts = [
        (run, load_json(run / "receipt.json")),
        (main_run, load_json(main_run / "receipt.json")),
    ]
    middle_records = {r["series_uid"]: r for r in receipts[0][1]["records"]}
    wanted = sorted({r["study_uid"] for _, rec in receipts for r in rec["records"]})
    if studies:
        wanted = [s for s in wanted if s in studies]
    corpus = open_corpus(root)
    for study_uid in wanted:
        study = read_study(corpus, study_uid)
        series = {s.row.series_uid: s for s in study.series}
        frames[study_uid] = {uid: series_frames(s) for uid, s in series.items()}
        geometry[study_uid] = {
            uid: {
                "view": list(middle_records[uid]["view"])
                if uid in middle_records
                else None,
                "n": len(s.slices),
                "middle": middle_records[uid]["slice_index"]
                if uid in middle_records
                else None,
                "knee": str(middle_records[uid]["assignments"].get("knee", ""))
                if uid in middle_records
                else "",
                "plane": frames[study_uid][uid]["plane"],
            }
            for uid, s in series.items()
        }
        cache: dict[Path, dict] = {}
        seen: set[tuple] = set()
        for _, receipt in receipts:
            for record in receipt["records"]:
                if record["study_uid"] != study_uid:
                    continue
                middle_record = middle_records.get(record["series_uid"], record)
                for o in record.get("observations", []):
                    if o["provenance"] != "native" or o["kind"] != "resolved":
                        continue
                    key = (
                        o["object"],
                        o["series_uid"],
                        tuple(o["slices"]),
                        o["support"],
                        o["row"],
                    )
                    if key in seen:
                        continue
                    seen.add(key)
                    path = next(
                        (
                            b / o["artifact"]
                            for b in (run, main_run)
                            if (b / o["artifact"]).exists()
                        ),
                        None,
                    )
                    row = {
                        "study_uid": study_uid,
                        "object": o["object"],
                        "series_uid": o["series_uid"],
                        "view": list(o["view"]),
                        "slice": int(o["slices"][0]),
                        "support": o["support"],
                        "row": o["row"],
                        "label": o["label"],
                        "artifact": o["artifact"],
                        "code": o["code"],
                        "count": o["count"],
                    }
                    own_slice = (
                        not o["artifact"]
                        .rsplit("/", 1)[-1]
                        .startswith(o["series_uid"] + ".npz")
                    )
                    row["selection"] = selection_of(o, middle_record, own_slice)
                    if path is None or o["series_uid"] not in series:
                        row["problem"] = "artifact_or_series_missing"
                        rows.append(row)
                        continue
                    if path not in cache:
                        with open_arrays(path, allow_pickle=False) as z:
                            cache[path] = {k: z[k] for k in z.files}
                    arrays = cache[path]
                    if o["support"] not in arrays:
                        row["problem"] = "support_not_saved"
                        rows.append(row)
                        continue
                    a = arrays[o["support"]]
                    if o["row"] is not None:
                        a = a[int(o["row"])]
                    if a.ndim != 2:
                        row["problem"] = f"support_is_{a.ndim}d"
                        rows.append(row)
                        continue
                    mask = (
                        (a == o["label"]) if o["label"] is not None else a.astype(bool)
                    )
                    pixels = int(np.count_nonzero(mask))
                    if o["count"] is not None and pixels != int(o["count"]):
                        row["problem"] = f"count_mismatch_saved_{pixels}"
                    slice_frames = frames[study_uid][o["series_uid"]]["frames"]
                    frame = (
                        slice_frames[row["slice"]]
                        if row["slice"] < len(slice_frames)
                        else None
                    )
                    if frame is None or not pixels:
                        row["problem"] = row.get("problem") or "no_frame_or_empty"
                        rows.append(row)
                        continue
                    places = frame.to_patient(np.argwhere(mask).astype(float))
                    normal = np.asarray(frame.normal(), dtype=float)
                    spacing = np.asarray(frame.spacing_rc, dtype=float)
                    row.update(
                        pixels=pixels,
                        area_mm2=float(pixels * spacing[0] * spacing[1]),
                        diagnostic_centroid_lps=[float(v) for v in places.mean(axis=0)],
                        low_lps=[float(v) for v in places.min(axis=0)],
                        high_lps=[float(v) for v in places.max(axis=0)],
                        normal_lps=[float(v) for v in normal],
                        plane_offset_mm=float(
                            np.asarray(frame.origin_lps, dtype=float) @ normal
                        ),
                        half_spacing_mm=half_step_mm(slice_frames, row["slice"]),
                    )
                    rows.append(row)
    return rows, geometry, frames


def load_key_planes(path: Path) -> dict:
    data = load_json(path)
    if data.get("schema") != KEY_PLANES_SCHEMA:
        raise SystemExit(f"{path}: schema is not {KEY_PLANES_SCHEMA}")
    return data["studies"]


def native_section(
    rows_index: dict, study: str, name: str, uid: str, z: int
) -> dict | None:
    """The run's largest native section of the object on exactly this series and slice, as information about the
    selected plane (None where the run resolved none there: that is not a refusal of the plane)."""
    found = rows_index.get((study, name, uid, z), [])
    if not found:
        return None
    best = max(found, key=lambda r: r["area_mm2"])
    return {k: best[k] for k in SECTION_KEYS if k in best}


def planes_for(
    study: str,
    name: str,
    spec: dict,
    series: dict,
    rows_index: dict,
) -> list[rel.KeyPlane]:
    """The object's key planes as the caller selected them, geometry from the actual acquisition. Every
    orientation is present: a selection not made is `not_supplied`."""
    planes: list[rel.KeyPlane] = []
    for orientation in rel.ORIENTATIONS:
        entries = spec.get(orientation)
        if entries is None:
            planes.append(rel.unresolved_plane(name, orientation, rel.NOT_SUPPLIED))
            continue
        for entry in entries if isinstance(entries, list) else [entries]:
            planes.append(plane_of_entry(study, name, orientation, entry, series))
    return planes


def plane_of_entry(
    study: str, name: str, orientation: str, entry: dict, series: dict
) -> rel.KeyPlane:
    outcome = entry.get("outcome", rel.SELECTED)
    common = {
        "reason": str(entry.get("reason", "")),
        "provenance": str(entry.get("provenance", "")),
    }
    if outcome != rel.SELECTED:
        return rel.unresolved_plane(
            name,
            orientation,
            outcome,
            candidates=[
                (c["series_uid"], c["slice"]) for c in entry.get("candidates", [])
            ],
            **common,
        )
    uid, z = str(entry.get("series_uid", "")), int(entry.get("slice", -1))
    precision = float(entry.get("precision_mm", math.nan))
    if "normal" in entry:
        return rel.key_plane(
            name,
            orientation,
            series_uid=uid,
            slice=z,
            normal=entry["normal"],
            origin_lps=entry.get("origin_lps"),
            offset_mm=entry.get("offset_mm"),
            precision_mm=precision,
            **common,
        )

    def bad(code: str) -> rel.KeyPlane:
        return rel.invalid_plane(
            name, orientation, code, series_uid=uid, slice=z, **common
        )

    info = series.get(uid)
    if info is None:
        return bad("series_not_in_study")
    if info["plane"].strip().lower() != orientation:
        return bad("orientation_disagrees_with_series")
    if not 0 <= z < len(info["frames"]):
        return bad("slice_out_of_range")
    frame = info["frames"][z]
    if frame is None:
        return bad("frame_unavailable")
    if math.isnan(precision):
        precision = half_step_mm(info["frames"], z)
    return rel.plane_of_frame(
        name,
        orientation,
        series_uid=uid,
        slice=z,
        frame=frame,
        precision_mm=precision,
        **common,
    )


def key_points(
    rows: list[dict],
    key_planes: dict,
    frames: dict,
) -> tuple[dict, dict[str, dict[str, rel.Position]]]:
    """Per study and object: the three-key-plane position (or the partial constraints), the actual source plane of
    each orientation, and the diagnostic section inventory. Objects are those the run resolved plus those the
    caller selected planes for."""
    rows_index: dict[tuple, list[dict]] = defaultdict(list)
    by_object: dict[tuple[str, str], list[dict]] = defaultdict(list)
    for r in rows:
        if "diagnostic_centroid_lps" in r:
            rows_index[
                (r["study_uid"], r["object"], r["series_uid"], r["slice"])
            ].append(r)
            by_object[(r["study_uid"], r["object"])].append(r)
    out: dict[str, dict] = defaultdict(dict)
    positions: dict[str, dict[str, rel.Position]] = defaultdict(dict)
    for study, series in sorted(frames.items()):
        names = sorted(
            {n for (s, n) in by_object if s == study} | set(key_planes.get(study, {}))
        )
        for name in names:
            spec = key_planes.get(study, {}).get(name, {})
            planes = planes_for(study, name, spec, series, rows_index)
            pos = rel.reference_position(name, planes)
            positions[study][name] = pos
            found = by_object.get((study, name), [])
            per_series = {
                uid: max(
                    (r for r in found if r["series_uid"] == uid),
                    key=lambda r: r["area_mm2"],
                )
                for uid in sorted({r["series_uid"] for r in found})
            }
            sources = {}
            for p in pos.planes:
                address = p.address()
                address["header_plane"] = series.get(p.series_uid, {}).get("plane")
                address["native_section"] = (
                    native_section(rows_index, study, name, p.series_uid, p.slice)
                    if p.usable
                    else None
                )
                sources.setdefault(p.orientation, []).append(address)
            out[study][name] = {
                "construction": CONSTRUCTION,
                "schema": SCHEMA,
                "status": pos.status,
                "geometry": pos.geometry,
                "complete": pos.complete,
                "position_lps": list(pos.point_lps) if pos.point_lps else None,
                "position_precision_mm": list(pos.precision_mm)
                if pos.precision_mm
                else None,
                "condition": None if math.isnan(pos.condition) else pos.condition,
                "rank": pos.rank,
                "line_direction_lps": list(pos.line_direction)
                if pos.line_direction
                else None,
                "planes": sources,
                "problems": dict(pos.problems),
                "distributed": name in DISTRIBUTED,
                "key_sections_role": "diagnostic_inventory_not_key_planes_not_consumed_for_position",
                "key_sections": {
                    uid: {k: r[k] for k in SECTION_KEYS if k in r}
                    for uid, r in per_series.items()
                },
            }
    return dict(out), positions


def vectors_and_images(
    positions: dict[str, dict[str, rel.Position]],
    frames: dict,
    knees: dict[str, str],
    scales: dict,
    pairs: bool,
) -> tuple[dict, dict]:
    """All-pairs vectors (when asked) and, per complete point, its nearest slice and in-plane place in every
    series of its study."""
    vectors: dict[str, dict] = {}
    images: dict[str, dict] = {}
    for study, objects in positions.items():
        given = scales.get(study)
        scale = (
            rel.knee_scale(given.get("mm"), str(given.get("source", "")))
            if given
            else rel.UNKNOWN_SCALE
        )
        if pairs:
            found, skipped = rel.pair_vectors(objects, scale, knees.get(study, ""))
            vectors[study] = {
                "scale": {"mm": scale.mm, "source": scale.source, "code": scale.code},
                "skipped": skipped,
                "vectors": [
                    {
                        "origin": v.origin,
                        "target": v.target,
                        "displacement_lps": list(v.displacement_lps),
                        "magnitude_mm": v.magnitude_mm,
                        "direction_lps": list(v.direction_lps)
                        if v.direction_lps
                        else None,
                        "direction_code": v.direction_code,
                        "normalized_displacement": list(v.normalized_displacement)
                        if v.normalized_displacement
                        else None,
                        "normalized_distance": v.normalized_distance,
                        "knee": v.knee,
                        "anatomical_axes": list(rel.ANATOMICAL_AXES),
                        "anatomical_mm": list(v.anatomical_mm)
                        if v.anatomical_mm
                        else None,
                        "orientation_code": v.orientation_code,
                    }
                    for v in found.values()
                ],
            }
        for name, pos in objects.items():
            if not pos.complete or pos.point_lps is None:
                continue
            images.setdefault(study, {})[name] = {
                uid: placement_row(
                    rel.locate_in_image(pos.point_lps, info["frames"], info["shape"])
                )
                for uid, info in frames[study].items()
            }
    return vectors, images


def placement_row(p: rel.ImagePlacement) -> dict:
    return {
        "status": p.status,
        "slice": p.slice,
        "off_plane_mm": p.off_plane_mm,
        "half_step_mm": p.half_step_mm,
        "rc": list(p.rc) if p.rc else None,
        "clipped_rc": list(p.clipped_rc) if p.clipped_rc else None,
        "in_stack": p.in_stack,
        "in_image": p.in_image,
        "tied_slices": list(p.tied_slices),
    }


def draw(
    study_uid: str,
    rows: list[dict],
    points: dict,
    positions: dict[str, dict[str, rel.Position]],
    frames: dict,
    root: Path,
    run: Path,
    main_run: Path,
    out: Path,
) -> None:
    """Per object with any selected plane: each source plane's actual image (the section the run resolved there,
    where it did, in cyan; the other selected planes' traces; the point), and the point carried onto every other
    series' nearest slice, titled by its off-plane distance and status."""
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    study = read_study(open_corpus(root), study_uid)
    series = {s.row.series_uid: s for s in study.series}
    out.mkdir(parents=True, exist_ok=True)
    colours = {"sagittal": "#ffd600", "coronal": "#00e676", "axial": "#ff9100"}
    for name, pos in sorted(positions.get(study_uid, {}).items()):
        if not pos.used:
            continue
        used_series = {p.series_uid for p in pos.used}
        others = [uid for uid in series if uid not in used_series]
        n_panels = len(pos.used) + (len(others) if pos.complete else 0)
        fig, axes = plt.subplots(1, n_panels, figsize=(4.2 * n_panels, 4.8))
        axes = list(np.atleast_1d(axes))
        for ax, plane in zip(axes, pos.used, strict=False):
            s = series[plane.series_uid]
            assert s.volume is not None
            frame = frames[study_uid][plane.series_uid]["frames"][plane.slice]
            img = np.asarray(s.volume[plane.slice])
            lo, hi = np.nanpercentile(img, [1, 99.5])
            ax.imshow(img, cmap="gray", vmin=lo, vmax=hi, interpolation="nearest")
            section = points[study_uid][name]["planes"][plane.orientation]
            native = next(
                (
                    a["native_section"]
                    for a in section
                    if a["series_uid"] == plane.series_uid
                ),
                None,
            )
            if native is not None:
                row = next(
                    r
                    for r in rows
                    if r["study_uid"] == study_uid
                    and r["object"] == name
                    and r["series_uid"] == plane.series_uid
                    and r["slice"] == plane.slice
                    and r["support"] == native["support"]
                    and r["row"] == native["row"]
                )
                mask = section_mask(row, run, main_run)
                if mask is not None and mask.any():
                    ax.contour(
                        mask.astype(float), [0.5], colors=["#00e5ff"], linewidths=1.0
                    )
            for other in pos.used:
                if other is plane:
                    continue
                trace = rel.plane_trace_in_frame(other, frame)
                if trace is None:
                    continue
                a, b, e = trace
                height, width = img.shape
                if abs(b) >= abs(a):  # column as a function of row
                    r = np.array([-0.5, height - 0.5])
                    c = (e - a * r) / b
                else:
                    c = np.array([-0.5, width - 0.5])
                    r = (e - b * c) / a
                ax.plot(c, r, "--", color=colours[other.orientation], lw=1.2)
            if pos.point_lps is not None:
                rc = frame.to_native(np.asarray(pos.point_lps)[None, :])[0]
                ax.plot(rc[1], rc[0], "+", color="#ff1744", ms=14, mew=2)
            ax.set_xlim(-0.5, img.shape[1] - 0.5)
            ax.set_ylim(img.shape[0] - 0.5, -0.5)
            ax.set_title(
                f"{name}: KEY PLANE {plane.orientation}\nslice {plane.slice} of {len(s.slices)}; "
                f"{'native section' if native else 'no native section here'}\n"
                f"dashed: the other key planes' traces; {plane.provenance or 'selection'}",
                fontsize=7,
            )
        if pos.complete and pos.point_lps is not None:
            for ax, uid in zip(axes[len(pos.used) :], others, strict=True):
                info = frames[study_uid][uid]
                placed = rel.locate_in_image(
                    pos.point_lps, info["frames"], info["shape"]
                )
                s = series[uid]
                assert s.volume is not None
                if placed.slice is None:
                    ax.set_title(f"{placed.status}", fontsize=7)
                    continue
                img = np.asarray(s.volume[placed.slice])
                lo, hi = np.nanpercentile(img, [1, 99.5])
                ax.imshow(img, cmap="gray", vmin=lo, vmax=hi, interpolation="nearest")
                if placed.rc is not None:
                    ax.plot(
                        placed.rc[1], placed.rc[0], "+", color="#ff1744", ms=14, mew=2
                    )
                ax.set_xlim(-0.5, img.shape[1] - 0.5)
                ax.set_ylim(img.shape[0] - 0.5, -0.5)
                plane_word = info["plane"]
                ax.set_title(
                    f"{plane_word} slice {placed.slice} of {len(info['frames'])}; "
                    f"{abs(placed.off_plane_mm or 0.0):.1f} mm off the plane\n{placed.status}",
                    fontsize=7,
                )
        for ax in axes:
            ax.set_xticks([])
            ax.set_yticks([])
        fig.suptitle(f"{name}: {pos.status} (construction {CONSTRUCTION})", fontsize=8)
        fig.tight_layout(rect=(0, 0, 1, 0.93))
        fig.savefig(out / f"{name}.png", dpi=100)
        plt.close(fig)


def section_mask(row: dict, run: Path, main_run: Path) -> np.ndarray | None:
    """The saved section a row describes (its artifact, support, row and label), for drawing."""
    path = next(
        (
            b / row["artifact"]
            for b in (run, main_run)
            if (b / row["artifact"]).exists()
        ),
        None,
    )
    if path is None:
        return None
    with open_arrays(path, allow_pickle=False) as z:
        a = z[row["support"]]
    if row["row"] is not None:
        a = a[int(row["row"])]
    return (a == row["label"]) if row["label"] is not None else a.astype(bool)


def main() -> None:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("--run", type=Path, required=True)
    parser.add_argument("--main-run", type=Path, required=True)
    parser.add_argument(
        "--out", type=Path, required=True, help="the table (JSON) written"
    )
    parser.add_argument(
        "--root",
        type=Path,
        default=KAGGLE_ROOT if KAGGLE_ROOT.is_dir() else ROOT / LOCAL_ROOT,
    )
    parser.add_argument(
        "--study-uid",
        nargs="*",
        default=None,
        help="only these studies (default: every one)",
    )
    parser.add_argument(
        "--key-planes",
        type=Path,
        default=None,
        help="the caller's selected key planes (JSON)",
    )
    parser.add_argument(
        "--knee-scale",
        type=Path,
        default=None,
        help="per study explicit knee scale (JSON)",
    )
    parser.add_argument(
        "--pairs", action="store_true", help="also write every ordered pair's vector"
    )
    parser.add_argument(
        "--draw", nargs="*", default=[], help="studies drawn (development only)"
    )
    parser.add_argument("--pictures", type=Path, default=None)
    args = parser.parse_args()
    rows, geometry, frames = sections_of(
        args.run,
        args.main_run,
        args.root,
        set(args.study_uid) if args.study_uid else None,
    )
    key_planes = load_key_planes(args.key_planes) if args.key_planes else {}
    unmatched = sorted(set(key_planes) - set(frames))
    points, positions = key_points(rows, key_planes, frames)
    knees = {
        study: next(
            (g["knee"] for g in series.values() if g.get("knee") in ("R", "L")), ""
        )
        for study, series in geometry.items()
    }
    scales = json.loads(args.knee_scale.read_text()) if args.knee_scale else {}
    vectors, images = vectors_and_images(positions, frames, knees, scales, args.pairs)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(
        json.dumps(
            {
                "schema": SCHEMA,
                "construction": CONSTRUCTION,
                "convention": __doc__,
                "key_planes_file": str(args.key_planes) if args.key_planes else None,
                "key_planes_studies_not_in_run": unmatched,
                "key_points": points,
                "pair_vectors": vectors,
                "images": images,
                "sections_diagnostic": rows,
                "series": geometry,
                "knees": knees,
            },
            default=str,
        )
    )
    problems = [r for r in rows if r.get("problem")]
    statuses: dict[str, int] = defaultdict(int)
    for objects in points.values():
        for record in objects.values():
            statuses[record["status"]] += 1
    print(
        f"{len(rows)} sections (diagnostic inventory); {len(problems)} with a problem; "
        f"objects by status: {dict(sorted(statuses.items()))}; construction={CONSTRUCTION}"
    )
    for r in problems[:40]:
        print(
            "  problem:",
            r["study_uid"][-8:],
            r["object"],
            r["support"],
            r["row"],
            r["problem"],
        )
    for study_uid in args.draw:
        assert args.pictures is not None
        draw(
            study_uid,
            rows,
            points,
            positions,
            frames,
            args.root,
            args.run,
            args.main_run,
            args.pictures / study_uid[-8:],
        )


if __name__ == "__main__":
    main()
