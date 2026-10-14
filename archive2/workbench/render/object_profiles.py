"""Draw a saved production measurement record. No substitute segmentation is computed."""

import argparse
import json
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np


def draw_record(axes, record, profile: int, title: str) -> None:
    """Arrange saved measurements and their explicit color annotations."""
    plane = record["acquired_plane"]
    axes[0].imshow(plane, cmap="gray")
    axes[0].set_title(title + "\nAcquired image")
    axes[1].imshow(plane, cmap="gray")
    if "background_mask" in record:
        rgba = np.zeros((*plane.shape, 4))
        rgba[record["background_mask"]] = (1.0, 0.18, 0.18, 1.0)
        axes[1].imshow(rgba, interpolation="nearest")
        split = record["background_split"]
        share = 100 * np.mean(record["background_mask"])
        axes[1].set_title(
            f"RED: recorded background split\nsplit={split:.2f}; {share:.1f}% of plane"
        )
    else:
        axes[1].set_title(
            "Background annotation unavailable\nNo mask supplied by this record"
        )
    axes[2].imshow(record["median"], cmap="gray", interpolation="nearest")
    axes[2].set_title("Physical squint: tile medians")
    axes[3].imshow(plane, cmap="gray")
    if "samples" in record:
        if not 0 <= profile < len(record["samples"]):
            raise ValueError("invalid_profile_index")
        point = record["points_rc"][profile]
        normal = record["normals_rc"][profile]
        sites = (
            point + record["distances_mm"][:, None] * normal / record["spacing_rc_mm"]
        )
        valid = record["valid"][profile]
        supported_sites = np.where(valid[:, None], sites, np.nan)
        axes[3].plot(
            supported_sites[:, 1],
            supported_sites[:, 0],
            ".-",
            color="#00e5ff",
            markersize=5,
            linewidth=2,
        )
        axes[3].plot(sites[~valid, 1], sites[~valid, 0], "mx", markersize=6)
        axes[3].set_xlim(-0.5, plane.shape[1] - 0.5)
        axes[3].set_ylim(plane.shape[0] - 0.5, -0.5)
        axes[3].set_title("CYAN: native samples\nMAGENTA: missing support")
        axes[4].plot(
            record["distances_mm"], record["samples"][profile], "o-", markersize=3
        )
        axes[4].set_title(f"Measured profile {profile}; gaps retained")
        axes[4].set_xlabel("Physical offset (mm)")
        axes[4].set_ylabel("Stored intensity")
    else:
        axes[3].set_title("Requested direction has no in-plane support")
        axes[4].text(0.5, 0.5, "No profile made\nAxis unavailable", ha="center")
    for axis in axes[:4]:
        axis.set_axis_off()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("record", type=Path)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--profile", type=int, required=True)
    parser.add_argument("--receipt", type=Path, required=True)
    args = parser.parse_args()
    receipt = json.loads(args.receipt.read_text())
    metadata = next(
        r
        for r in receipt["records"]
        if (args.receipt.parent / r.get("artifact", f"{r['series_uid']}.npz")).resolve()
        == args.record.resolve()
    )
    with np.load(args.record, allow_pickle=False) as arrays:
        record = dict(arrays)
        record["spacing_rc_mm"] = np.asarray(metadata["spacing_rc_mm"])
        record["background_split"] = metadata.get("background_split")
        fig, axes = plt.subplots(1, 5, figsize=(20, 4), layout="constrained")
        draw_record(axes, record, args.profile, "/".join(metadata["view"]))
        args.out.parent.mkdir(parents=True, exist_ok=True)
        fig.savefig(args.out, dpi=160)
        plt.close(fig)


if __name__ == "__main__":
    main()
