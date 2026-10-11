"""Render a source-linked image series from a saved production Packet A run."""

import argparse
import json
from hashlib import sha256
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

from workbench.render.object_profiles import draw_record


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("run", type=Path)
    parser.add_argument("--study-uid", required=True)
    parser.add_argument("--probe-fraction-rc", type=float, nargs=2, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    fraction = np.asarray(args.probe_fraction_rc)
    if (
        not np.all(np.isfinite(fraction))
        or np.any(fraction < 0)
        or np.any(fraction > 1)
    ):
        parser.error("probe fractions must lie in [0,1]")
    receipt_path = args.run / "receipt.json"
    receipt = json.loads(receipt_path.read_text())
    records = [
        r
        for r in receipt["records"]
        if r["study_uid"] == args.study_uid and "acquired_plane" in r["arrays"]
    ]
    if not records:
        parser.error("no saved acquired planes for this study")
    args.out.mkdir(parents=True, exist_ok=True)
    gallery, axes = plt.subplots(
        len(records),
        5,
        figsize=(20, 4 * len(records)),
        layout="constrained",
        squeeze=False,
    )
    panels = []
    for row, metadata in enumerate(records):
        artifact = args.run / metadata.get("artifact", f"{metadata['series_uid']}.npz")
        with np.load(artifact, allow_pickle=False) as arrays:
            record = dict(arrays)
        for name, descriptor in metadata["arrays"].items():
            array = record[name]
            digest = sha256(
                array.dtype.str.encode() + str(array.shape).encode() + array.tobytes()
            ).hexdigest()
            if digest != descriptor["digest"]:
                raise ValueError("saved_array_digest_mismatch")
        record["spacing_rc_mm"] = np.asarray(metadata["spacing_rc_mm"])
        record["background_split"] = metadata.get("background_split")
        target = fraction * (np.asarray(record["acquired_plane"].shape) - 1)
        profile = (
            int(np.argmin(np.sum((record["points_rc"] - target) ** 2, axis=1)))
            if "points_rc" in record
            else 0
        )
        view, fluid, fat = metadata["view"]
        title = f"{view} · fluid-sensitive={fluid}, fat-suppressed={fat}"
        draw_record(axes[row], record, profile, title)
        figure, one_axes = plt.subplots(1, 5, figsize=(20, 4), layout="constrained")
        draw_record(one_axes, record, profile, title)
        name = f"{row + 1:02d}-{view.lower()}-fs{fluid}-fat{fat}.png"
        figure.savefig(args.out / name, dpi=160)
        plt.close(figure)
        panels.append(
            {
                "image": name,
                "artifact": str(artifact),
                "artifact_sha256": sha256(artifact.read_bytes()).hexdigest(),
                "source_plane": metadata["source_plane"],
                "slice_index": metadata["slice_index"],
                "profile_index": profile,
                "profile_site_rc": record["points_rc"][profile].tolist()
                if "points_rc" in record
                else None,
            }
        )
    gallery.suptitle(
        "Packet A: acquired image → RED background annotation → squint → CYAN samples → measured profile",
        fontsize=17,
    )
    gallery.savefig(args.out / "series.png", dpi=160)
    plt.close(gallery)
    manifest = {
        "schema": "packet-a-visuals-v2",
        "color_legend": {
            "red": "saved mask from the production regime's whole-series background split",
            "cyan": "supported native profile sample locations",
            "magenta": "missing profile support",
        },
        "receipt_sha256": sha256(receipt_path.read_bytes()).hexdigest(),
        "renderer_sha256": sha256(Path(__file__).read_bytes()).hexdigest(),
        "layout_sha256": sha256(
            Path(__file__).with_name("object_profiles.py").read_bytes()
        ).hexdigest(),
        "probe_fraction_rc": fraction.tolist(),
        "scope": "all saved middle planes in the chosen study; red background-split mask, cyan samples, magenta missing support",
        "panels": panels,
    }
    (args.out / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    print(
        json.dumps(
            {
                "images": len(panels),
                "series": str((args.out / "series.png").resolve()),
                "manifest": str((args.out / "manifest.json").resolve()),
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
