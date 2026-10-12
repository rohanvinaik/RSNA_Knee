"""Color image series from saved production boundary-census records; nothing measured here.

Three panels per acquired plane, which are the census's own readings in order:

    1. the territories, with every native edge drawn in the colour of WHAT LIES ACROSS it --
       cyan where a territory meets measured dark, orange where it meets a peer territory,
       magenta at the frame. The loop's composition, seen rather than tabulated.
    2. each territory's MEASURED SHARE: the fraction of its loop resting on a dark reading
       rather than on a constructed divide.
    3. the relief between touching territories: each pair's pass against the weaker centre's
       height above it, coloured by its named code. A pair that was not read is absent, never
       plotted at zero.

Every value is one `knee.objects.boundaries` already returned and `knee.pictures.objects` already
arranged. This file positions axes and chooses colours; it measures, thresholds and segments
nothing, and it never maps a pair back onto pixels, because the stage does not compute that.
"""

import argparse
import json
from hashlib import sha256
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

from knee.objects.boundaries import PAIR_CODE_VALUES
from knee.pictures.objects import census_panels, measured_share

EDGE_COLOURS = {
    1: ("#00e5ff", "measured dark"),
    2: ("#ff9e00", "a peer territory"),
    3: ("#ff00ff", "missing acquisition"),
    4: ("#ff00ff", "the frame"),
    5: ("#9d4edd", "unseeded material"),
}
CODE_COLOURS = {
    "read": "#00e5ff",
    "no_divide": "#6c757d",
    "too_few_sites": "#ffd166",
    "peak_below_saddle": "#ef476f",
    "unreadable_relief": "#ff00ff",
    "invalid_measurement": "#ef476f",
}


def draw_census(axes, arrays) -> None:
    panels = census_panels(
        arrays["b1_labels"],
        arrays["b1_edge_points_rc"],
        arrays["b1_edge_kinds"],
        arrays["b1_census_edges_by_kind"],
        arrays["b1_census_pair_saddle_mm"],
        arrays["b1_census_prominence_mm"],
        arrays["b1_census_pair_codes"],
    )
    plane = arrays["acquired_plane"]
    labels = panels.territories

    axes[0].imshow(plane, cmap="gray")
    tint = plt.colormaps["tab20"](((labels - 1) % 20) / 19)
    tint[..., 3] = np.where(labels > 0, 0.35, 0)
    axes[0].imshow(tint, interpolation="nearest")
    points, kinds = panels.edge_points, panels.edge_kinds
    for value, (colour, _) in EDGE_COLOURS.items():
        chosen = kinds == value
        if chosen.any():
            axes[0].scatter(
                points[chosen, 1], points[chosen, 0], c=colour, s=0.35, linewidths=0
            )
    axes[0].set_axis_off()
    axes[0].set_title(
        "Native edges by WHAT LIES ACROSS\nCYAN: measured dark · ORANGE: a peer territory",
        fontsize=9,
    )

    share = measured_share(panels)
    seen = np.isfinite(share)
    axes[1].barh(np.arange(len(share))[seen], share[seen], color="#00e5ff", height=0.8)
    axes[1].set_xlim(0, 1)
    axes[1].set_xlabel("share of loop on a measured dark reading", fontsize=8)
    axes[1].set_ylabel("territory", fontsize=8)
    axes[1].invert_yaxis()
    axes[1].tick_params(labelsize=7)
    axes[1].set_title(
        "Measured share of each territory's loop\n(the rest is constructed divide)",
        fontsize=9,
    )

    saddle, prominence = panels.saddle_mm, panels.prominence_mm
    codes = panels.pair_codes
    if len(saddle):
        weaker = np.min(prominence, axis=1)
        for name, value in PAIR_CODE_VALUES.items():
            chosen = codes == value
            if not chosen.any():
                continue
            height = weaker[chosen]
            drawn = np.isfinite(height)
            axes[2].scatter(
                saddle[chosen][drawn],
                height[drawn],
                c=CODE_COLOURS[name],
                s=9,
                label=f"{name} ({int(chosen.sum())})",
                linewidths=0,
            )
        axes[2].legend(fontsize=6, loc="upper right", framealpha=0.3)
    axes[2].set_xlabel("the pass between them (mm)", fontsize=8)
    axes[2].set_ylabel("weaker centre above the pass (mm)", fontsize=8)
    axes[2].tick_params(labelsize=7)
    axes[2].set_title(
        "The relief between touching territories\nan unread pair is absent, never zero",
        fontsize=9,
    )


def draw(run: Path, study_uid: str, out: Path) -> dict:
    """Draw this stage from the saved run and return its manifest.

    The one entry a caller uses, so the single command can draw every stage without knowing each
    renderer's argument spelling. `main()` is a thin wrapper over it, so the hand-typed command
    and the joined run draw the same thing from the same code.
    """
    receipt_path = run / "receipt.json"
    receipt = json.loads(receipt_path.read_text())
    records = [
        r
        for r in receipt["records"]
        if r["study_uid"] == study_uid and "boundaries" in r
    ]
    if not records:
        raise ValueError("no production boundary-census records for the selected study")
    out.mkdir(parents=True, exist_ok=True)
    gallery, axes = plt.subplots(
        len(records),
        3,
        figsize=(15, 4.2 * len(records)),
        squeeze=False,
        layout="constrained",
    )
    panels = []
    for row, record in enumerate(records):
        artifact = run / record["artifact"]
        with np.load(artifact, allow_pickle=False) as saved:
            arrays = dict(saved)
        for name, descriptor in record["arrays"].items():
            a = arrays[name]
            digest = sha256(
                a.dtype.str.encode() + str(a.shape).encode() + a.tobytes()
            ).hexdigest()
            if digest != descriptor["digest"]:
                raise ValueError("saved_array_digest_mismatch")
        draw_census(axes[row], arrays)
        view, fluid, fat = record["view"]
        title = (
            f"{view} · fluid-sensitive={fluid}, fat-suppressed={fat} · "
            f"slice {record['slice_index']}"
        )
        one, one_axes = plt.subplots(1, 3, figsize=(15, 4.2), layout="constrained")
        draw_census(one_axes, arrays)
        one.suptitle(title)
        name = f"{row + 1:02d}-{view.lower()}-fs{fluid}-fat{fat}.png"
        one.savefig(out / name, dpi=150)
        plt.close(one)
        panels.append(
            {
                "image": name,
                "artifact": record["artifact"],
                "artifact_sha256": sha256(artifact.read_bytes()).hexdigest(),
                "source_plane": record["source_plane"],
                "slice_index": record["slice_index"],
                "boundaries": record["boundaries"],
            }
        )
    gallery.suptitle(
        "What bounds each territory → its measured share → the relief between neighbours",
        fontsize=16,
    )
    gallery.savefig(out / "series.png", dpi=140)
    plt.close(gallery)
    manifest = {
        "schema": "boundary-census-visuals",
        "receipt_sha256": sha256(receipt_path.read_bytes()).hexdigest(),
        "renderer_sha256": sha256(Path(__file__).read_bytes()).hexdigest(),
        "panels": panels,
        "scope": "saved census values arranged; no anatomy and no admission inferred by the renderer",
        "image_sha256": {
            p.name: sha256(p.read_bytes()).hexdigest()
            for p in sorted(out.glob("*.png"))
        },
    }
    (out / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    return manifest


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("run", type=Path)
    parser.add_argument("--study-uid", required=True)
    parser.add_argument(
        "--out", type=Path, default=Path("data/pictures/object-toolkit/boundaries")
    )
    args = parser.parse_args()
    try:
        manifest = draw(args.run, args.study_uid, args.out)
    except ValueError as refusal:
        parser.error(str(refusal))
    print(
        json.dumps(
            {
                "series": str((args.out / "series.png").resolve()),
                "panels": len(manifest["panels"]),
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
