"""Development pictures of the anatomical reference and the patella search that reads relative to
it (never part of the production run; it reads the receipt and arrays a run saved, and the acquired
slices from the corpus).

`.venv/bin/python scripts/draw_reference_first.py --run <interiors dir> --study-uid <uid> --out <dir>`
draws, at the slices' own pixels: the reference's key plane (the acquired slice with the bone's
region the lens named on it outlined, and the cheap profile through depth with the key slice marked),
and the patella search (the fat-suppressed series' profile through depth with the expected
neighbourhood, the slices read and the planes asked marked; each plane that named the patella with
its region, the tendons and the pads outlined), beside the twin's slice of the same place where the
tendons were read."""

from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from knee.array_archive import open_arrays
from knee.json_store import load_json
from knee.objects.assignments import OBJECT_CODES
from knee.study.corpus import (
    KAGGLE_ROOT,
    LOCAL_ROOT,
    open_corpus,
    read_study,
)

ROOT = Path(__file__).resolve().parent.parent
COLOURS = {
    "patella": "#00e5ff",
    "patellar_tendon": "#ffd600",
    "quadriceps_tendon": "#ff6d00",
    "hoffa_fat_pad": "#76ff03",
    "suprapatellar_fat": "#d500f9",
}


def outline(ax, mask: np.ndarray, colour: str, label: str | None = None) -> None:
    if mask.any():
        ax.contour(mask.astype(float), [0.5], colors=[colour], linewidths=1.2)
        if label:
            ax.plot([], [], color=colour, label=label)


def show(ax, plane: np.ndarray, title: str) -> None:
    low, high = np.nanpercentile(plane, [1, 99.5])
    ax.imshow(plane, cmap="gray", vmin=low, vmax=high, interpolation="nearest")
    ax.set_title(title, fontsize=8)
    ax.set_xticks([])
    ax.set_yticks([])


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run", type=Path, required=True)
    parser.add_argument("--study-uid", required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument(
        "--root",
        type=Path,
        default=KAGGLE_ROOT if KAGGLE_ROOT.is_dir() else ROOT / LOCAL_ROOT,
    )
    args = parser.parse_args()
    receipt = load_json(args.run / "receipt.json")
    records = [r for r in receipt["records"] if r["study_uid"] == args.study_uid]
    study = read_study(open_corpus(args.root), args.study_uid)
    series = {s.row.series_uid: s for s in study.series}
    arrays = {}
    try:
        for record in records:
            previous = arrays.pop(record["series_uid"], None)
            if previous is not None:
                previous.close()
            arrays[record["series_uid"]] = open_arrays(
                args.run / record["artifact"], allow_pickle=False
            )
        _draw_reference(args, records, series, arrays)
    finally:
        for archive in arrays.values():
            archive.close()


def _draw_reference(args, records, series, arrays) -> None:
    args.out.mkdir(parents=True, exist_ok=True)
    for record in records:
        ref = record.get("reference") or {}
        if ref.get("code") != "reference_confirmed":
            continue
        saved, vol = arrays[record["series_uid"]], series[record["series_uid"]].volume
        bone = ref["bone"]
        fig, axes = plt.subplots(1, 3, figsize=(15, 5))
        profile = saved[f"a3_{bone}_profile_area_mm2"]
        axes[0].plot(profile, marker="o", ms=3)
        for z in ref["slices"]:
            axes[0].axvline(z, color="r")
        axes[0].set_title(
            f"{bone} supported marrow area through depth; key slice {ref['slices']}",
            fontsize=8,
        )
        axes[0].set_xlabel("slice")
        axes[0].set_ylabel("mm2 (NaN: not read)")
        z = ref["slices"][0]
        assert vol is not None
        plane = np.asarray(vol[z])
        show(axes[1], plane, f"{ref['view']} slice {z}: acquired")
        show(axes[2], plane, f"{bone} region the lens named, slice {z}")
        slices = list(saved[f"a3_{bone}_plane_slices"])
        if z == record["slice_index"]:
            region = saved["a1_objects"] == OBJECT_CODES[bone]
        else:
            region = saved[f"a3_{bone}_plane_region"][slices.index(z)]
        outline(axes[2], region, "#00e5ff")
        axes[2].text(
            2,
            plane.shape[0] - 4,
            f"{ref['reason']}",
            fontsize=5,
            color="yellow",
            wrap=True,
        )
        fig.tight_layout()
        fig.savefig(
            args.out / f"reference-{record['series_uid'][-8:]}-{bone}-slice{z}.png",
            dpi=110,
        )
        plt.close(fig)
    for record in records:
        search = (record.get("patella") or {}).get("search")
        if not search:
            continue
        saved, vol = arrays[record["series_uid"]], series[record["series_uid"]].volume
        planes = [p for p in record["patella"]["pointed_planes"] if not p["middle"]]
        named = [(row, p) for row, p in enumerate(planes) if p["code"] == "identified"]
        fig, axes = plt.subplots(
            1, 1 + max(1, len(named)), figsize=(5 * (1 + max(1, len(named))), 5)
        )
        axes = np.atleast_1d(axes)
        area = saved["a3_patella_profile_area_mm2"]
        window = saved["a3_patella_search_window"]
        visited = saved["a3_patella_search_visited"]
        axes[0].plot(area, marker="o", ms=3, label="profile (NaN: unvisited)")
        if not window.all():
            axes[0].axvspan(
                np.min(np.flatnonzero(window)) - 0.5,
                np.max(np.flatnonzero(window)) + 0.5,
                color="orange",
                alpha=0.2,
                label="expected neighbourhood",
            )
        axes[0].plot(
            np.flatnonzero(~visited),
            np.zeros(int((~visited).sum())),
            "kx",
            label="never visited",
        )
        for z in search["planes_read_natively"]:
            axes[0].axvline(z, color="r", ls="--")
        axes[0].set_title(
            f"patella search: {search['code']}; asked {search['planes_read_natively']}",
            fontsize=8,
        )
        axes[0].legend(fontsize=6)
        for k, (row, p) in enumerate(named):
            ax = axes[k + 1]
            z = p["slice"]
            assert vol is not None
            plane = np.asarray(vol[z])
            show(ax, plane, f"FS slice {z}: patella {p['patella_pixels']} px")
            objects = saved["a3_patella_plane_objects"][row]
            for name, colour in COLOURS.items():
                outline(ax, objects == OBJECT_CODES[name], colour, name)
            ax.legend(fontsize=5, loc="lower left")
        fig.tight_layout()
        fig.savefig(
            args.out / f"patella-search-{record['series_uid'][-8:]}.png", dpi=110
        )
        plt.close(fig)


if __name__ == "__main__":
    main()
