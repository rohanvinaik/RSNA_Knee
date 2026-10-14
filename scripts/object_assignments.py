"""Draw the named objects from saved production records: the lenses that named them, and the names.

Per series, four panels: the acquired signal; the field's lenses (the unrecorded margin, the
record's edge, low signal outside the body's outline, and the outline); every territory's walled
part, coloured by its bone answer, with its depth, signal third and wall share at its deepest
place; and the named objects with each question's code. Nothing is decided here: every colour is
read from the saved arrays and the receipt.
"""

import argparse
import json
from hashlib import sha256
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

from knee.objects.assignments import OBJECT_CODES

OBJECT_COLOURS = {
    "air": (0.25, 0.55, 1.0, 0.5),
    "skin": (1.0, 0.9, 0.1, 1.0),
    "femur": (1.0, 0.55, 0.1, 0.55),
    "tibia": (0.2, 0.85, 0.35, 0.55),
    "joint": (0.95, 0.2, 0.95, 0.65),
}
BONE_COLOURS = {
    "bone_concurred": (0.1, 0.8, 0.3, 0.55),
    "abstain_signal_silent": (0.65, 0.95, 0.4, 0.5),
    "not_bone": (0.55, 0.55, 0.55, 0.35),
    "abstain_signs_disagree": (1.0, 0.55, 0.0, 0.55),
    "abstain_wall_unread": (1.0, 0.85, 0.3, 0.45),
}


def overlay(axis, mask, colour):
    rgba = np.zeros((*mask.shape, 4))
    rgba[mask] = colour
    axis.imshow(rgba, interpolation="nearest")


def draw_stages(axes, arrays, record):
    plane = arrays["acquired_plane"]
    assigned = record["assignments"]
    codes = assigned["codes"]
    for ax in axes:
        ax.set_axis_off()
    axes[0].imshow(plane, cmap="gray")
    axes[0].set_title("Acquired signal", fontsize=9)
    margin, inside = arrays["a1_margin"], arrays["a1_inside"]
    axes[1].imshow(plane, cmap="gray")
    overlay(axes[1], margin, (0.2, 0.4, 1.0, 1.0))
    overlay(axes[1], arrays["a1_record_edge"], (0.6, 0.85, 1.0, 0.55))
    overlay(axes[1], arrays["b1_dark"] & ~inside & ~margin, (1.0, 0.12, 0.12, 0.75))
    if inside.any() and not inside.all():
        axes[1].contour(
            inside.astype(float), levels=[0.5], colors="#ffd166", linewidths=0.6
        )
    axes[1].set_title(
        "BLUE unrecorded · PALE record edge\nRED low signal outside the outline · YELLOW outline",
        fontsize=9,
    )
    walled = arrays["a1_walled"]
    axes[2].imshow(plane, cmap="gray")
    rgba = np.zeros((*walled.shape, 4))
    for t in assigned["territories"]:
        rgba[walled == t["territory"]] = BONE_COLOURS[t["bone"]]
    axes[2].imshow(rgba, interpolation="nearest")
    for t in assigned["territories"]:
        row, col = t["peak_rc"]
        third = "·" if t["signal_third"] is None else f"{t['signal_third']:+d}"
        share = t["wall_share"]
        wall = "—" if share is None or not np.isfinite(share) else f"{share:.2f}"
        axes[2].text(
            col,
            row,
            f"{t['territory']}: {t['depth_mm']:.0f}mm {third} w{wall}",
            color="white",
            fontsize=5.5,
            ha="center",
        )
    axes[2].set_title(
        "Walled territories: depth · signal third · wall share\n"
        "GREEN bone · PALE walled, signal silent · GREY not bone · ORANGE/GOLD open",
        fontsize=9,
    )
    objects = arrays["a1_objects"]
    axes[3].imshow(plane, cmap="gray")
    for name, colour in OBJECT_COLOURS.items():
        overlay(axes[3], objects == OBJECT_CODES[name], colour)
    axes[3].set_title(
        f"BLUE air: {codes['air']} · YELLOW skin: {codes['skin']}\n"
        f"ORANGE femur, GREEN tibia: {codes['pair']}\nMAGENTA joint: {codes['joint']}",
        fontsize=8,
    )


def draw(run: Path, study_uid: str, out: Path) -> dict:
    """Draw the assignments of one study from the saved run and return the manifest."""
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
        4,
        figsize=(18, 4.8 * len(records)),
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
        one, one_axes = plt.subplots(1, 4, figsize=(22, 6), layout="constrained")
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
                "counts": record["assignments"]["counts"],
            }
        )
    gallery.suptitle(
        "The field's lenses → the territories' lenses → the named objects", fontsize=16
    )
    gallery.savefig(out / "series.png", dpi=120)
    plt.close(gallery)
    manifest = {
        "schema": "assignment-visuals-a1",
        "receipt_sha256": sha256(receipt_path.read_bytes()).hexdigest(),
        "renderer_sha256": sha256(Path(__file__).read_bytes()).hexdigest(),
        "panels": panels,
        "scope": "every selected native plane; objects named only where the saved lenses concur",
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
