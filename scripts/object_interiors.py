"""Color image series from saved production B1 records; no segmentation here."""

import argparse
import json
from hashlib import sha256
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.collections import LineCollection

from knee.receipt import digest

# The three stage pictures, each two of a slice's six panels.
STAGES = (
    ("01-surrounding-field", (0, 1)),
    ("02-interiors", (2, 3)),
    ("03-native-traces", (4, 5)),
)


def overlay_mask(axis, mask, color):
    rgba = np.zeros((*mask.shape, 4))
    rgba[mask] = color
    axis.imshow(rgba, interpolation="nearest")


def draw_stages(axes, arrays):
    plane = arrays["acquired_plane"]
    dark, available = arrays["b1_dark"], arrays["b1_available"]
    labels, markers = arrays["b1_labels"], arrays["b1_markers"]
    for ax in axes:
        ax.set_axis_off()
    axes[0].imshow(plane, cmap="gray")
    axes[0].set_title("Acquired signal")
    axes[1].imshow(plane, cmap="gray")
    overlay_mask(axes[1], dark, (1, 0.12, 0.12, 1))
    overlay_mask(axes[1], ~available, (1, 0, 1, 1))
    axes[1].set_title("RED: measured low signal\nMAGENTA: unavailable")
    axes[2].imshow(arrays["b1_distance_mm"], cmap="magma")
    for region in np.unique(markers):
        if region:
            site = np.argwhere(markers == region).mean(axis=0)
            axes[2].plot(site[1], site[0], "+", color="#00e5ff", markersize=8)
    axes[2].set_title("Distance from surrounding constraints\nCYAN: interior peaks")
    axes[3].imshow(plane, cmap="gray")
    rgba = plt.colormaps["tab20"](((labels - 1) % 20) / 19)
    rgba[..., 3] = np.where(labels > 0, 0.5, 0)
    axes[3].imshow(rgba, interpolation="nearest")
    for region in np.unique(markers):
        if region:
            site = np.argwhere(markers == region).mean(axis=0)
            axes[3].text(
                site[1], site[0], str(region), color="white", fontsize=7, ha="center"
            )
    axes[3].set_title("All proposed interiors\nIDs are territories, not tissue names")
    points = arrays["b1_edge_points_rc"]
    normals = arrays["b1_edge_normals_rc"]
    codes = arrays["b1_trace_codes"]
    axes[4].imshow(plane, cmap="gray")
    axes[5].imshow(plane, cmap="gray")
    if len(points):
        tangent = np.column_stack((-normals[:, 1], normals[:, 0]))
        tangent /= np.max(np.abs(tangent), axis=1)[:, None]
        segments = np.stack((points - tangent / 2, points + tangent / 2), axis=1)[
            :, :, ::-1
        ]
        axes[4].add_collection(
            LineCollection(segments, colors="#00e5ff", linewidths=0.65)
        )
        for code, color in (
            (2, "#ffd166"),
            (3, "#ff9e00"),
            (4, "#ff00ff"),
            (5, "#ff00ff"),
        ):
            selected = codes == code
            axes[5].add_collection(
                LineCollection(
                    segments[selected], colors=color, linewidths=0.5, alpha=0.75
                )
            )
        good = codes == 1
        trace = arrays["b1_trace_points_rc"][good]
        axes[5].scatter(trace[:, 1], trace[:, 0], c="#00e5ff", s=0.6)
    for ax in axes[4:]:
        ax.set_xlim(-0.5, plane.shape[1] - 0.5)
        ax.set_ylim(plane.shape[0] - 0.5, -0.5)
    axes[4].set_title("Original native territory edges")
    axes[5].set_title(
        "CYAN: observed dark-band traces\nYELLOW: open · ORANGE: multiple\nMAGENTA: missing or clipped"
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
        if r["study_uid"] == study_uid and "interiors" in r
    ]
    if not records:
        raise ValueError("no production interior records for the selected study")
    out.mkdir(parents=True, exist_ok=True)
    gallery, axes = plt.subplots(
        len(records),
        6,
        figsize=(24, 4 * len(records)),
        squeeze=False,
        layout="constrained",
    )
    # Separate stage series make every additional operation inspectable across views.
    stages = {
        name: plt.subplots(
            len(records),
            2,
            figsize=(10, 4 * len(records)),
            squeeze=False,
            layout="constrained",
        )
        for name, _ in STAGES
    }
    panels = []
    for row, record in enumerate(records):
        artifact = run / record["artifact"]
        with np.load(artifact, allow_pickle=False) as saved:
            arrays = dict(saved)
        for name, descriptor in record["arrays"].items():
            if digest(arrays[name]) != descriptor["digest"]:
                raise ValueError("saved_array_digest_mismatch")
        draw_stages(axes[row], arrays)
        view, fluid, fat = record["view"]
        axes[row, 0].set_ylabel(f"{view} fs={fluid} fat={fat}")
        title = f"{view} · fluid-sensitive={fluid}, fat-suppressed={fat} · slice {record['slice_index']}"
        axes[row, 0].set_title(title + "\nAcquired signal", fontsize=10)
        one, one_axes = plt.subplots(1, 6, figsize=(24, 4), layout="constrained")
        draw_stages(one_axes, arrays)
        one.suptitle(title)
        name = f"{row + 1:02d}-{view.lower()}-fs{fluid}-fat{fat}.png"
        one.savefig(out / name, dpi=150)
        plt.close(one)
        # Draw once into a dedicated full layout, then copy its raster panels into each stage.
        scratch, scratch_axes = plt.subplots(1, 6)
        draw_stages(scratch_axes, arrays)
        scratch.set_size_inches(24, 4)
        scratch.canvas.draw()
        pixels = np.asarray(scratch.canvas.buffer_rgba())
        for stage_name, columns in STAGES:
            stage_axes = stages[stage_name][1]
            for col, index in enumerate(columns):
                box = scratch_axes[index].get_window_extent().bounds
                x, y, w, h = map(int, box)
                stage_axes[row, col].imshow(
                    pixels[pixels.shape[0] - y - h : pixels.shape[0] - y, x : x + w]
                )
                stage_axes[row, col].set_title(
                    scratch_axes[index].get_title(), fontsize=10
                )
                stage_axes[row, col].set_axis_off()
            stage_axes[row, 0].set_title(
                f"{view} · fs={fluid} · fat={fat} · slice {record['slice_index']}\n"
                + scratch_axes[columns[0]].get_title(),
                fontsize=10,
            )
        plt.close(scratch)
        panels.append(
            {
                "image": name,
                "artifact": record["artifact"],
                "artifact_sha256": sha256(artifact.read_bytes()).hexdigest(),
                "source_plane": record["source_plane"],
                "slice_index": record["slice_index"],
                "interiors": record["interiors"],
            }
        )
    gallery.suptitle(
        "Surrounding information → geometric interiors → native border readings",
        fontsize=18,
    )
    gallery.savefig(out / "series.png", dpi=140)
    plt.close(gallery)
    for stage_name, _ in STAGES:
        stage = stages[stage_name][0]
        stage.savefig(out / f"{stage_name}.png", dpi=140)
        plt.close(stage)
    manifest = {
        "schema": "interior-visuals-b1",
        "receipt_sha256": sha256(receipt_path.read_bytes()).hexdigest(),
        "renderer_sha256": sha256(Path(__file__).read_bytes()).hexdigest(),
        "stages": [
            "01-surrounding-field.png",
            "02-interiors.png",
            "03-native-traces.png",
        ],
        "panels": panels,
        "scope": "all selected native planes; no anatomical ownership inferred by renderer",
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
        "--out", type=Path, default=Path("data/pictures/object-toolkit/interiors-b1")
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
