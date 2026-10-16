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
from knee.receipt import digest

# Each part's colour in the pictures, with the one word the legend calls it by. No two parts share a
# word or a colour (`tests/test_part_colours.py`): a part is told from its neighbours by its colour.
OBJECT_COLOURS = {
    "air": ("BLUE", (0.25, 0.55, 1.0, 0.45)),
    "skin": ("YELLOW", (1.0, 0.9, 0.1, 1.0)),
    "femur": ("ORANGE", (1.0, 0.55, 0.1, 0.55)),
    "tibia": ("GREEN", (0.2, 0.85, 0.35, 0.55)),
    "joint": ("MAGENTA", (0.95, 0.2, 0.95, 0.7)),
    "patella": ("CYAN", (0.0, 0.85, 1.0, 0.6)),
    "meniscus": ("WHITE", (1.0, 1.0, 1.0, 0.9)),
    "medial_meniscus": ("RED", (1.0, 0.15, 0.15, 0.9)),
    "lateral_meniscus": ("LIME", (0.6, 1.0, 0.0, 0.95)),
    "fibula": ("VIOLET", (0.6, 0.3, 1.0, 0.75)),
    "femoral_cartilage": ("CREAM", (1.0, 1.0, 0.7, 0.85)),
    "tibial_cartilage": ("TEAL", (0.0, 0.75, 0.6, 0.85)),
    "pcl": ("CRIMSON", (0.85, 0.1, 0.35, 0.8)),
    "acl": ("ROYAL BLUE", (0.15, 0.3, 1.0, 0.8)),
    "mcl": ("HOT PINK", (1.0, 0.25, 0.7, 0.9)),
    "lcl": ("ORANGE-RED", (1.0, 0.3, 0.0, 0.8)),
    "joint_fluid": ("SKY BLUE", (0.55, 0.85, 1.0, 0.85)),
    "hoffa_fat_pad": ("APRICOT", (1.0, 0.75, 0.45, 0.65)),
    "suprapatellar_fat": ("LEMON", (1.0, 0.95, 0.4, 0.6)),
    "medial_gastrocnemius": ("OLIVE", (0.6, 0.65, 0.1, 0.6)),
    "lateral_gastrocnemius": ("BRIGHT GREEN", (0.1, 1.0, 0.2, 0.75)),
    "popliteal_artery": ("FUCHSIA", (1.0, 0.0, 0.6, 0.9)),
    "popliteal_vein": ("TURQUOISE", (0.25, 0.88, 0.82, 0.9)),
    "semimembranosus": ("BROWN", (0.65, 0.35, 0.1, 0.9)),
    "patellar_tendon": ("MINT", (0.5, 1.0, 0.75, 0.85)),
    "quadriceps_tendon": ("LAVENDER", (0.8, 0.7, 1.0, 0.85)),
    "subcutaneous_fat": ("PLUM", (0.55, 0.25, 0.55, 0.55)),
    "muscle": ("SALMON", (0.98, 0.5, 0.45, 0.5)),
    "anterior_synovial_recess": ("INDIGO", (0.3, 0.05, 0.7, 0.75)),
    "synovium": ("PEAR", (0.8, 0.95, 0.2, 1.0)),
    "joint_capsule": ("SPRING GREEN", (0.0, 1.0, 0.55, 1.0)),
    "gastrocnemius_semimembranosus_bursa": ("PURPLE", (0.7, 0.0, 1.0, 0.75)),
    "semitendinosus": ("SILVER", (0.7, 0.7, 0.7, 0.9)),
}
# The legend's word for each part's colour.
WORDS = {name: word for name, (word, _) in OBJECT_COLOURS.items()}


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
    named = (
        assigned["femur"],
        assigned["tibia"],
        assigned.get("patella"),  # records older than the patella's naming lack it
        assigned.get("fibula"),
        assigned.get("acl"),
        assigned.get("lcl"),
        assigned.get("medial_gastrocnemius"),
        assigned.get("lateral_gastrocnemius"),
    )
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
        "Territories and their strongest peaks\nRINGED: the territories named as bones",
        fontsize=9,
    )
    for name, (_, colour) in OBJECT_COLOURS.items():
        mask = arrays.get(f"a2_{name}")
        overlay(
            axes[2], objects == OBJECT_CODES[name] if mask is None else mask, colour
        )
    axes[2].set_title(
        f"{WORDS['air']} air · {WORDS['skin']} skin: {codes['air']}\n"
        f"{WORDS['femur']} femur · {WORDS['tibia']} tibia · {WORDS['joint']} joint: "
        f"{codes['femur']}\n"
        f"{WORDS['patella']} patella: {codes['patella']}\n"
        f"{WORDS['medial_meniscus']} medial · {WORDS['lateral_meniscus']} lateral · "
        f"{WORDS['meniscus']} unsided meniscus: {codes['meniscus']}, "
        f"sides {codes.get('meniscus_side', '-')}"
        + (
            f"\n{WORDS['femoral_cartilage']} femoral · "
            f"{WORDS['tibial_cartilage']} tibial cartilage: {codes['cartilage']}"
            if "cartilage" in codes
            else ""
        )
        + (f"\n{WORDS['pcl']} PCL: {codes['pcl']}" if "pcl" in codes else "")
        + (
            f"\n{WORDS['fibula']} fibula: {codes['fibula']}"
            if "fibula" in codes
            else ""
        )
        + (f"\n{WORDS['acl']} ACL: {codes['acl']}" if "acl" in codes else "")
        + (f"\n{WORDS['mcl']} MCL: {codes['mcl']}" if "mcl" in codes else "")
        + (f"\n{WORDS['lcl']} LCL: {codes['lcl']}" if "lcl" in codes else "")
        + (
            f"\n{WORDS['joint_fluid']} joint fluid: {codes['joint_fluid']}"
            if "joint_fluid" in codes
            else ""
        )
        + (
            f"\n{WORDS['hoffa_fat_pad']} Hoffa's fat pad: {codes['hoffa_fat_pad']}"
            if "hoffa_fat_pad" in codes
            else ""
        )
        + (
            f"\n{WORDS['suprapatellar_fat']} suprapatellar fat: "
            f"{codes['suprapatellar_fat']}"
            if "suprapatellar_fat" in codes
            else ""
        )
        + (
            f"\n{WORDS['patellar_tendon']} patellar · "
            f"{WORDS['quadriceps_tendon']} quadriceps tendon: "
            + (
                codes["patellar_tendon"]
                if codes["patellar_tendon"] == codes.get("quadriceps_tendon")
                else f"{codes['patellar_tendon']}, {codes.get('quadriceps_tendon', '-')}"
            )
            if "patellar_tendon" in codes
            else ""
        )
        + (
            f"\n{WORDS['subcutaneous_fat']} fat under the skin: "
            f"{codes['subcutaneous_fat']}"
            if "subcutaneous_fat" in codes
            else ""
        )
        + (
            f"\n{WORDS['muscle']} muscle: {codes['muscle']}"
            if "muscle" in codes
            else ""
        )
        + (
            f"\n{WORDS['anterior_synovial_recess']} anterior recess: "
            f"{codes['anterior_synovial_recess']}"
            if "anterior_synovial_recess" in codes
            else ""
        )
        + (
            f"\n{WORDS['synovium']} synovial surface: {codes['synovium']}"
            if "synovium" in codes
            else ""
        )
        + (
            f"\n{WORDS['joint_capsule']} joint capsule: {codes['joint_capsule']}"
            if "joint_capsule" in codes
            else ""
        )
        + (
            f"\n{WORDS['medial_gastrocnemius']} medial gastrocnemius head: "
            f"{codes['medial_gastrocnemius']}"
            if "medial_gastrocnemius" in codes
            else ""
        )
        + (
            f"\n{WORDS['lateral_gastrocnemius']} lateral gastrocnemius head: "
            f"{codes['lateral_gastrocnemius']}"
            if "lateral_gastrocnemius" in codes
            else ""
        )
        + (
            f"\n{WORDS['popliteal_artery']} popliteal artery lumen: "
            f"{codes['popliteal_artery']}"
            if "popliteal_artery" in codes
            else ""
        )
        + (
            f"\n{WORDS['popliteal_vein']} popliteal vein lumen: "
            f"{codes['popliteal_vein']}"
            if "popliteal_vein" in codes
            else ""
        )
        + (
            f"\n{WORDS['semimembranosus']} semimembranosus tendon: "
            f"{codes['semimembranosus']}"
            if "semimembranosus" in codes
            else ""
        )
        + (
            f"\n{WORDS['semitendinosus']} semitendinosus tendon: "
            f"{codes['semitendinosus']}"
            if "semitendinosus" in codes
            else ""
        )
        + (
            f"\n{WORDS['gastrocnemius_semimembranosus_bursa']} "
            "gastrocnemius-semimembranosus bursa: "
            f"{codes['gastrocnemius_semimembranosus_bursa']}"
            if "gastrocnemius_semimembranosus_bursa" in codes
            else ""
        ),
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
            if digest(arrays[name]) != descriptor["digest"]:
                raise ValueError("saved_array_digest_mismatch")
        draw_stages(axes[row], arrays, record)
        view, fluid, fat = record["view"]
        title = f"{view} · fluid-sensitive={fluid}, fat-suppressed={fat} · slice {record['slice_index']}"
        if "main_slice" in record:
            title += f" · the {record['main_slice']['object']}'s main slice"
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
