"""Draw the named objects from saved production records, beside the lenses they were read from.

Per series, three panels: the acquired signal; the territories with each one's strongest interior
peak (the femur's and tibia's ringed); and the named objects. Nothing is decided here: every colour
is read from the saved arrays and the receipt.
"""

import argparse
import json
from hashlib import sha256
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

from knee.objects.assignments import OBJECT_CODES

OBJECT_COLOURS = {
    "air": (0.25, 0.55, 1.0, 0.45),
    "skin": (1.0, 0.9, 0.1, 1.0),
    "femur": (1.0, 0.55, 0.1, 0.55),
    "tibia": (0.2, 0.85, 0.35, 0.55),
    "joint": (0.95, 0.2, 0.95, 0.7),
}


def overlay(axis, mask, colour):
    rgba = np.zeros((*mask.shape, 4))
    rgba[mask] = colour
    axis.imshow(rgba, interpolation="nearest")


def draw_stages(axes, arrays, record):
    plane = arrays["acquired_plane"]
    labels, objects = arrays["b1_labels"], arrays["a1_objects"]
    assigned = record["assignments"]
    codes = assigned["codes"]
    for ax in axes:
        ax.imshow(plane, cmap="gray")
        ax.set_axis_off()
    axes[0].set_title("Acquired signal", fontsize=9)
    rgba = plt.colormaps["tab20"](((labels - 1) % 20) / 19)
    rgba[..., 3] = np.where(labels > 0, 0.45, 0)
    axes[1].imshow(rgba, interpolation="nearest")
    named = (assigned["femur"], assigned["tibia"])
    for peak in assigned["peaks"]:
        row, col = peak["peak_rc"]
        ringed = peak["territory"] in named
        axes[1].plot(
            col,
            row,
            "o" if ringed else "+",
            color="white" if ringed else "#00e5ff",
            markersize=9 if ringed else 6,
            fillstyle="none",
        )
        axes[1].text(
            col + 4,
            row,
            f"{peak['territory']}: {peak['depth_mm']:.0f} mm",
            color="white",
            fontsize=6,
        )
    axes[1].set_title(
        "Territories and their strongest peaks\nRINGED: the deepest, and the deepest above or below it",
        fontsize=9,
    )
    for name, colour in OBJECT_COLOURS.items():
        overlay(axes[2], objects == OBJECT_CODES[name], colour)
    axes[2].set_title(
        f"BLUE air · YELLOW skin: {codes['air']}\n"
        f"ORANGE femur · GREEN tibia · MAGENTA joint: {codes['femur']}",
        fontsize=8,
    )


def draw(run: Path, study_uid: str, out: Path) -> dict:
    """Draw the named objects of one study from the saved run and return the manifest."""
    receipt_path = run / "receipt.json"
    receipt = json.loads(receipt_path.read_text())
    records = [
        r
        for r in receipt["records"]
        if r["study_uid"] == study_uid and "assignments" in r
    ]
    if not records:
        raise ValueError("no assignment records for the selected study")
    out.mkdir(parents=True, exist_ok=True)
    gallery, axes = plt.subplots(
        len(records),
        3,
        figsize=(15, 5 * len(records)),
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
        draw_stages(axes[row], arrays, record)
        view, fluid, fat = record["view"]
        title = f"{view} · fluid-sensitive={fluid}, fat-suppressed={fat} · slice {record['slice_index']}"
        axes[row, 0].set_title(title + "\nAcquired signal", fontsize=9)
        one, one_axes = plt.subplots(1, 3, figsize=(18, 6), layout="constrained")
        draw_stages(one_axes, arrays, record)
        one.suptitle(title)
        name = f"{row + 1:02d}-{view.lower()}-fs{fluid}-fat{fat}.png"
        one.savefig(out / name, dpi=150)
        plt.close(one)
        panels.append(
            {
                "image": name,
                "artifact": record["artifact"],
                "artifact_sha256": sha256(artifact.read_bytes()).hexdigest(),
                "codes": record["assignments"]["codes"],
            }
        )
    gallery.suptitle("Territories and peaks → the named objects", fontsize=16)
    gallery.savefig(out / "series.png", dpi=120)
    plt.close(gallery)
    manifest = {
        "schema": "assignment-visuals-a1",
        "receipt_sha256": sha256(receipt_path.read_bytes()).hexdigest(),
        "renderer_sha256": sha256(Path(__file__).read_bytes()).hexdigest(),
        "panels": panels,
        "scope": "every selected native plane; colours read from the saved arrays and receipt",
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
    parser.add_argument("--out", type=Path, default=Path("data/pictures/assignments"))
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
